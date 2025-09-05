// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

contract ContentSentinel {
    enum Decision { Pending, Remove, Label, Allow }
    enum VoteChoice { Remove, Label, Allow }

    struct Tally {
        uint256 removeVotes;
        uint256 labelVotes;
        uint256 allowVotes;
        Decision decision;
        bool finalized;
    }

    struct Moderator {
        uint256 reputation; // simple integer reputation
        mapping(bytes32 => bool) hasVoted; // contentHash => voted?
    }

    mapping(address => Moderator) public moderators;
    mapping(bytes32 => Tally) public tallies; // contentHash => tally
    address public admin;
    uint256 public minVotesToFinalize = 5;

    event Voted(bytes32 indexed contentHash, address indexed mod, VoteChoice choice);
    event Finalized(bytes32 indexed contentHash, Decision decision);
    event ReputationUpdated(address indexed mod, int256 delta, uint256 newRep);

    modifier onlyAdmin() { require(msg.sender == admin, "admin"); _; }

    constructor() {
        admin = msg.sender;
        moderators[msg.sender].reputation = 100;
    }

    function seedModerator(address mod, uint256 rep) external onlyAdmin {
        moderators[mod].reputation = rep;
        emit ReputationUpdated(mod, int256(rep), rep);
    }

    function vote(bytes32 contentHash, VoteChoice choice) external {
        Moderator storage m = moderators[msg.sender];
        require(m.reputation > 0, "not moderator or rep 0");
        require(!m.hasVoted[contentHash], "already voted");
        require(!tallies[contentHash].finalized, "finalized");

        m.hasVoted[contentHash] = true;
        Tally storage t = tallies[contentHash];

        if (choice == VoteChoice.Remove) t.removeVotes += m.reputation;
        else if (choice == VoteChoice.Label) t.labelVotes += m.reputation;
        else t.allowVotes += m.reputation;

        emit Voted(contentHash, msg.sender, choice);

        uint256 votes = t.removeVotes + t.labelVotes + t.allowVotes;
        if (votes >= minVotesToFinalize) {
            // determine decision by highest weighted votes
            if (t.removeVotes >= t.labelVotes && t.removeVotes >= t.allowVotes) {
                t.decision = Decision.Remove;
            } else if (t.labelVotes >= t.removeVotes && t.labelVotes >= t.allowVotes) {
                t.decision = Decision.Label;
            } else {
                t.decision = Decision.Allow;
            }
            t.finalized = true;
            // reputation updates (toy logic)
            _updateReputations(contentHash, t.decision);
            emit Finalized(contentHash, t.decision);
        }
    }

    function _updateReputations(bytes32 contentHash, Decision finalDecision) internal {
        // NOTE: In a real system you’d track voters per contentHash to adjust their rep.
        // For brevity this demo omits per-voter logging. Add an event log & offchain calc,
        // then adjust via an admin batch call (or more complex onchain storage).
    }

    function getTally(bytes32 contentHash) external view returns (Tally memory) {
        return tallies[contentHash];
    }

    function setMinVotes(uint256 n) external onlyAdmin {
        minVotesToFinalize = n;
    }
}