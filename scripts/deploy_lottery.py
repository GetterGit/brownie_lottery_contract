from brownie import Lottery, config, network
from eth_account import Account
from scripts.helpful_scripts import get_account, get_contract, fund_with_link
import time

# since we parameterized all variables in helpful scrips, we don't need to put any conditions on whether we are deploying to local or testnet or mainnet below
def deploy_lottery():
    account = get_account()
    lottery = Lottery.deploy(
        get_contract("eth_usd_price_feed").address,
        get_contract("vrf_coordinator").address,
        get_contract("link_token").address,
        config["networks"][network.show_active()]["fee"],
        config["networks"][network.show_active()]["keyHash"],
        {"from": account},
        # if there is no 'verify' key, default to False
        publish_source=config["networks"][network.show_active()].get("verify", False),
    )
    print("The lottery contract has been deployed!")
    return lottery


# starting the lottery for the most recently deployed contract
def start_lottery():
    account = get_account()
    lottery = Lottery[-1]
    lottery_start = lottery.startLottery({"from": account})
    # brownie is sometimes confused if we don't wait for the last tx to go through
    lottery_start.wait(1)
    print("The lottery has started!")


def enter_lottery():
    account = get_account()
    lottery = Lottery[-1]
    value_to_send = lottery.getEntranceFee() + 1e8
    lottery_enter = lottery.enter({"from": account, "value": value_to_send})
    lottery_enter.wait(1)
    print("We have enterred the lottery!")


def end_lottery():
    account = get_account()
    lottery = Lottery[-1]
    # before ending the lottery, we need some Link token to cover the requestRandomness() reuquest within the endLottery() function
    # 1. fund the contract with Link
    # 2. end the lottery
    fund_tx = fund_with_link(lottery.address)
    fund_tx.wait(1)
    lottery_end = lottery.endLottery({"from": account})
    lottery_end.wait(1)
    print("The lottery has ended!")
    # however, we are now waiting for the callbal from the Chainlink node which will respond with fulfillRandomness()
    # typically, 60 sec is enough for the Chainlink node to respond
    time.sleep(180)
    # the recentWinner variable gets updated as a result of fulfillRandomness() execution
    print(f"{lottery.recentWinner()} is the new winner!")


def main():
    deploy_lottery()
    start_lottery()
    enter_lottery()
    end_lottery()
