from condorcet import CondorcetSystem
from pygraph.classes.digraph import digraph
from pygraph.algorithms.cycles import find_cycle
import copy
class RankedPairs(CondorcetSystem):
    
    @staticmethod
    def calculateWinner(ballots):
        result = CondorcetSystem.calculateWinner(ballots)
        
        # If there's a Condorcet winner, return it
        if "winners" in result:
            return result
        
        # Initialize the candidate graph
        result["rounds"] = []
        tieBreaker = RankedPairs.generateTieBreaker(result["candidates"])
        candidateGraph = digraph()
        candidateGraph.add_nodes(list(result["candidates"]))
        
        # Loop until we've considered all possible pairs
        remainingStrongPairs = copy.deepcopy(result["strongPairs"])
        while len(remainingStrongPairs) > 0:
            round = {}
            
            # Find the strongest pair
            largestStrength = max(remainingStrongPairs.values())
            strongestPairs = set()
            for pair in remainingStrongPairs.keys():
                if remainingStrongPairs[pair] == largestStrength:
                    strongestPairs.add(pair)
            if len(strongestPairs) > 1:
                result["tieBreaker"] = tieBreaker
                round["tiedPairs"] = strongestPairs
                strongestPair = RankedPairs.breakStrongestPairTie(strongestPairs, tieBreaker)
            else:
                strongestPair = list(strongestPairs)[0]
            round["pair"] = strongestPair
            
            # If the pair would add a cycle, skip it
            candidateGraph.add_edge(strongestPair[0], strongestPair[1])
            if len(find_cycle(candidateGraph)) > 0:
                round["action"] = "skipped"
                candidateGraph.del_edge(strongestPair[0], strongestPair[1])
            else:
                round["action"] = "added"
            del remainingStrongPairs[strongestPair]
            result["rounds"].append(round)
        
        # The winner is any candidate with no losses (if there are 2+, use the tiebreaker)
        winners = result["candidates"].copy()
        for edge in candidateGraph.edges():
            if edge[1] in winners:
                winners.remove(edge[1])
        
        # Mark the winner
        if len(winners) == 1:
            result["winners"] = set([list(winners)[0]])
        else:
            result["tiedWinners"] = winners
            result["tieBreaker"] = tieBreaker
            result["winners"] = set([RankedPairs.breakWinnerTie(winners, tieBreaker)])
        
        # Return the final result
        return result