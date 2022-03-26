from brownie import network
from scripts.helpful_scripts import (
    LOCAL_BLOCKCHAIN_ENVIRONMENTS,
    get_account,
    fund_with_link,
)
from scripts.deploy_lottery import deploy_lottery
import pytest
import time


def test_can_pick_winner():
    # we wanna run this test only on a live chain like Rinkeby
    if network.show_active() in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip()
    # Arrange
    lottery = deploy_lottery()
    account = get_account()
    lottery.startLottery({"from": account})
    # emulating 2 people entering the lottery (can add another account here for sanity)
    lottery.enter({"from": account, "value": lottery.getEntranceFee()})
    lottery.enter({"from": account, "value": lottery.getEntranceFee()})
    fund_with_link(lottery)
    lottery.endLottery({"from": account})
    starting_balance_acc = account.balance()
    balance_of_lottery = lottery.balance()
    # Act
    # waiting 60 sec for the Chainlink's node callback
    time.sleep(180)
    assert lottery.recentWinner() == account
    assert lottery.balance() == 0
    assert account.balance() == starting_balance_acc + balance_of_lottery
