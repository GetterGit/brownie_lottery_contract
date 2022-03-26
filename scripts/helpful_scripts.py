# importing the Contract package to use it when getting ABI of desired testnet/mainnet contracts
# importing 'interface' to work with the Link token interface within the fund_with_link() function
#   the interfaces will essentially replace the need for Contract.from_abi() in the get_contract() function
from brownie import (
    accounts,
    network,
    config,
    MockV3Aggregator,
    VRFCoordinatorMock,
    LinkToken,
    Contract,
    interface,
)

FORKED_LOCAL_ENVIRONMENTS = ["mainnet-fork", "mainnet"]
LOCAL_BLOCKCHAIN_ENVIRONMENTS = ["development", "genache-local"]

# if we pass 'index' to the function, we will use the index from the accounts['index'] variable
# if we pass 'id', we will have accounts.load('id')
def get_account(index=None, id=None):
    if index:
        return accounts[index]
    elif id:
        return accounts.load(id)
    elif (
        network.show_active() in LOCAL_BLOCKCHAIN_ENVIRONMENTS
        or network.show_active() in FORKED_LOCAL_ENVIRONMENTS
    ):
        return accounts[0]
    else:
        return accounts.add(config["wallets"]["from_key"])


# mapping contract names to contract types
contract_to_mock = {
    "eth_usd_price_feed": MockV3Aggregator,
    "vrf_coordinator": VRFCoordinatorMock,
    "link_token": LinkToken,
}


def get_contract(contract_name):
    """This function will grab the contract addresses from the brownie config
    if defined. Otherwise, it will deploy a mock version of that contract,
    and return that mock contract.

        Args:
            contract_name (string)

        Returns:
            brownie.network.contract.ProjectContract: The most recently deployed
            version of this contract - [-1].
    """
    contract_type = contract_to_mock[contract_name]
    if network.show_active() in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        # checking whether the mock has already been deployed
        if len(contract_type) <= 0:
            deploy_mocks()
        # now, we wanna get the deployed mock
        contract = contract_type[-1]
    # now, we also wanna be getting a contract when deploying on testnets, and we don't need mock here, but rather have this contract address in our config file
    else:
        contract_address = config["networks"][network.show_active()][contract_name]
        # address - just got it from the above line of code
        # ABI - got it from deploying the mock to the local env
        # Contract.from_abi allows us to get a contract from its ABI and address
        contract = Contract.from_abi(
            contract_type._name, contract_address, contract_type.abi
        )

    #
    return contract


# setting up params for the mock price feed aggregator as its on-chain version returns the 8-decimal precision
DECIMALS = 8
INITIAL_VALUE = 2000 * 1e8


def deploy_mocks(decimals=DECIMALS, initial_value=INITIAL_VALUE):
    account = get_account()
    MockV3Aggregator.deploy(decimals, initial_value, {"from": account})
    # since VRFCoordinator requires the Link token address, we firstly deploy the Link token and then get its address for VRFCoordinator
    link_token = LinkToken.deploy({"from": account})
    VRFCoordinatorMock.deploy(link_token.address, {"from": account})
    print("All mocks have been deployed!")


def fund_with_link(
    contract_address, account=None, link_token=None, amount=100000000000000000
):
    # we will use the account passed as the 'account' argument, else we will use get_account()
    account = account if account else get_account()
    # same for the Link token
    link_token = link_token if link_token else get_contract("link_token")
    # the below line is using get_contract() to get the link token contract, so I'm commenting them out because I've used the LINK interface
    # fund_tx = link_token.transfer(contract_address, amount, {"from": account})
    # using the Link token interface for the funding tx
    link_token_contract = interface.LinkTokenInterface(link_token.address)
    fund_tx = link_token_contract.transfer(contract_address, amount, {"from": account})
    fund_tx.wait(1)
    print("The contract has been funded with 0.1 LINK.")
    return fund_tx
