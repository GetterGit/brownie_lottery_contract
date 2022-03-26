// SPDX-License-Identifier: MIT
pragma solidity ^0.6.6;

import "@chainlink/contracts/src/v0.6/interfaces/AggregatorV3Interface.sol";
import "@chainlink/contracts/src/v0.6/VRFConsumerBase.sol";
import "@openzeppelin/contracts/access/Ownable.sol";

contract Lottery is VRFConsumerBase, Ownable {
    address payable[] public players;
    address payable public recentWinner;
    uint256 public recentRandomNumber;
    // creating the USD entry fee vatiable to declare its value in the contructor
    uint256 public usdEntryFee;
    // internal meaning only
    AggregatorV3Interface internal ethUsdPriceFeed;
    // representing the lottery states: OPEN = 0, CLOSED = 1, CALCULATING_WINNER = 2
    enum LOTTERY_STATE {
        OPEN,
        CLOSED,
        CALCULATING_WINNER
    }
    LOTTERY_STATE public lottery_state;

    // adding variables for VRFConsumerBase: fee payable to the oracle and the unique id of the oracle's node
    uint256 public fee;
    bytes32 public keyHash;

    // creating an event to be emitted when the contract sends a randomness request as a result of endLottery() execution
    event RequestedRandomness(bytes32 requestId);

    // adding VRFConsumerBase constructor to our constructor : https://github.com/smartcontractkit/chainlink/blob/develop/contracts/src/v0.8/VRFConsumerBase.sol
    constructor(
        address _priceFeedAddress,
        address _vrfCoordinator,
        address _link,
        uint256 _fee,
        bytes32 _keyHash
    ) public VRFConsumerBase(_vrfCoordinator, _link) {
        usdEntryFee = 50 * 1e18;
        ethUsdPriceFeed = AggregatorV3Interface(_priceFeedAddress);
        lottery_state = LOTTERY_STATE.CLOSED;
        fee = _fee;
        keyHash = _keyHash;
    }

    // user to enter the lottery
    function enter() public payable {
        require(
            lottery_state == LOTTERY_STATE.OPEN,
            "The lottery is not open yet."
        );
        // $50 minimum
        require(
            msg.value >= getEntranceFee(),
            "Please, submit at least $50 in ETH to enter."
        );
        players.push(msg.sender);
    }

    // to retrieve the entrance fee
    function getEntranceFee() public view returns (uint256) {
        (, int256 price, , , ) = ethUsdPriceFeed.latestRoundData();
        // * 1e10 to get the value to 18 decimals as the price is returned with 8 decimals only
        uint256 adjustedPrice = uint256(price) * 1e10;
        // now, calculating the ETH value of the USD entry fee
        uint256 costToEnter = (usdEntryFee * 1e18) / adjustedPrice;
        return costToEnter;
    }

    // admin to start the lottery
    function startLottery() public onlyOwner {
        require(
            lottery_state == LOTTERY_STATE.CLOSED,
            "Can't start a new lottery yet!"
        );
        lottery_state = LOTTERY_STATE.OPEN;
    }

    // admin to end the lottery
    function endLottery() public onlyOwner {
        lottery_state = LOTTERY_STATE.CALCULATING_WINNER;
        // we are now calling the function inherited from the VRFConsumerBase contract
        // here, we have the request call sent to the oracle's node
        bytes32 requestId = requestRandomness(keyHash, fee);
        emit RequestedRandomness(requestId);
        // now, the oracle's node is sending the callback to return us the random number in another function
    }

    // making this function internal because we only want it to be called by the randomness oracle (technically it's the oracle's node calling VRFCoordinator which calls this function within our conract)
    // override means we are overriding the original declaration of fulfullRandomness()
    function fulfillRandomness(bytes32 _requestId, uint256 _randomness)
        internal
        override
    {
        require(
            lottery_state == LOTTERY_STATE.CALCULATING_WINNER,
            "You are not calculating the winner yet."
        );
        require(_randomness > 0, "The random number hasn't been found");
        // finding the index of winner with the modulo operation
        uint256 indexOfWinner = _randomness % players.length;
        // now, finding the winner by the index
        recentWinner = players[indexOfWinner];
        // transferring the lottery funds to the winner
        recentWinner.transfer(address(this).balance);
        //resetting the lottery with the new players array of size 0 and closing the lottery
        players = new address payable[](0);
        lottery_state = LOTTERY_STATE.CLOSED;
        recentRandomNumber = _randomness;
    }
}
