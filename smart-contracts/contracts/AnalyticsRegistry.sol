// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

contract AnalyticsRegistry {
    mapping(bytes32 => uint256) public riskScores;
    mapping(bytes32 => string) public riskLevels;
    mapping(bytes32 => uint256) public lastUpdated;
    
    address public admin;
    
    event RiskScoreUpdated(address indexed wallet, uint256 score, string level);
    
    constructor() {
        admin = msg.sender;
    }
    
    modifier onlyAdmin() {
        require(msg.sender == admin, "Only admin");
        _;
    }
    
    function updateRiskScore(
        address wallet,
        uint256 score,
        string memory level
    ) external onlyAdmin {
        require(score <= 100, "Score must be 0-100");
        
        bytes32 walletHash = keccak256(abi.encodePacked(wallet));
        riskScores[walletHash] = score;
        riskLevels[walletHash] = level;
        lastUpdated[walletHash] = block.timestamp;
        
        emit RiskScoreUpdated(wallet, score, level);
    }
    
    function getRiskScore(address wallet) external view returns (uint256, string memory) {
        bytes32 walletHash = keccak256(abi.encodePacked(wallet));
        return (riskScores[walletHash], riskLevels[walletHash]);
    }
    
    function getRiskScoreWithTimestamp(address wallet) external view returns (uint256, string memory, uint256) {
        bytes32 walletHash = keccak256(abi.encodePacked(wallet));
        return (riskScores[walletHash], riskLevels[walletHash], lastUpdated[walletHash]);
    }
    
    function transferAdmin(address newAdmin) external onlyAdmin {
        require(newAdmin != address(0), "Invalid address");
        admin = newAdmin;
    }
}
