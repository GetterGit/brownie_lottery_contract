from brownie import Lottery, accounts, config, network, exceptions
from scripts.deploy_lottery import deploy_lottery
from scripts.helpful_scripts import (
    LOCAL_BLOCKCHAIN_ENVIRONMENTS,
    get_account,
    fund_with_link,
    get_contract,
)
import pytest
from web3 import Web3

# Unit Tests: a way of testing the smallest pieces of code in an isolated instance.
# e.g. independent functions
# Integration Tests: a way of testing across multiple complex instances
# e.g. a scope of functions


def test_get_entrance_fee():
    # we wanna do this test only for our local environment
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip()
    # Arrange
    lottery = deploy_lottery()
    # Act
    # 3145 USD : 1 ETH
    # usdEntryFee = 50 USD => usdEntryFee ~ 0,01589
    lowest_expected_entrance_fee = Web3.toWei(0.01589, "ether")
    highest_expected_entrance_fee = Web3.toWei(0.03, "ether")
    entrance_fee = lottery.getEntranceFee()
    # Assert
    assert (
        entrance_fee >= lowest_expected_entrance_fee
        and entrance_fee <= highest_expected_entrance_fee
    )


def test_cant_enter_unless_started():
    # we wanna do this test only for our local environment
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip()
    # Arrange
    lottery = deploy_lottery()
    # Act / Assert
    with pytest.raises(exceptions.VirtualMachineError):
        lottery.enter({"from": get_account(), "value": lottery.getEntranceFee()})


def test_can_start_and_enter_lottery():
    # we wanna do this test only for our local environment
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip()
    # Arrange
    lottery = deploy_lottery()
    account = get_account()
    # Act
    lottery.startLottery({"from": account})
    lottery.enter({"from": account, "value": lottery.getEntranceFee()})
    # Assert
    assert lottery.players(0) == account


def test_can_end_lottery():
    # we wanna do this test only for our local environment
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip()
    # Arrange
    lottery = deploy_lottery()
    account = get_account()
    lottery.startLottery({"from": account})
    lottery.enter({"from": account, "value": lottery.getEntranceFee()})
    fund_with_link(lottery)
    # Act
    lottery.endLottery({"from": account})
    # Assert
    assert lottery.lottery_state() == 2


def test_can_pick_winner_correctly():
    # we wanna do this test only for our local environment
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip()
    # Arrange
    lottery = deploy_lottery()
    account = get_account()
    lottery.startLottery({"from": account})
    lottery.enter({"from": account, "value": lottery.getEntranceFee()})
    # we can do get_account(index) since we are testing in our local Ganache instance
    lottery.enter({"from": get_account(index=1), "value": lottery.getEntranceFee()})
    lottery.enter({"from": get_account(index=2), "value": lottery.getEntranceFee()})
    fund_with_link(lottery)
    lottery_end_tx = lottery.endLottery({"from": account})
    # now, we want to look for the RequestedRandomness event ad find its requestId
    request_id = lottery_end_tx.events["RequestedRandomness"]["requestId"]
    # Act
    # now, we can pretend to be a chainlink node and use request_id in our callback to fulfil randomness
    STATIC_RANDOM_NUMBER = 2141
    # getting VRFCoordinatorMock from helpful scripts and using its callBackWithRandomness function
    get_contract("vrf_coordinator").callBackWithRandomness(
        request_id, STATIC_RANDOM_NUMBER, lottery.address, {"from": account}
    )
    # The winner should be calculated as 2141 % 3 = 2, so get_account(index=2) shall be the winner
    starting_balance_acc2 = get_account(index=2).balance()
    balance_of_lottery = lottery.balance()
    # Assert
    assert lottery.recentWinner() == get_account(index=2)
    assert lottery.balance() == 0
    assert get_account(index=2).balance() == starting_balance_acc2 + balance_of_lottery
