# Copyright (C) 2009, Brad Beattie
# 
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
# 
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

from BaseHTTPServer import BaseHTTPRequestHandler, HTTPServer
from plurality import Plurality
from plurality_at_large import PluralityAtLarge
from irv import IRV
from stv import STV 
from ranked_pairs import RankedPairs
from schulze_method import SchulzeMethod
import json, types, StringIO, traceback

# This class provides a basic server to listen for JSON requests. It then
# calculates the winner using the desired voting system and returns the results,
# again, encoded in JSON.
class ElectionRequestHandler(BaseHTTPRequestHandler):


    def do_GET(self):
        response = '<html><body><h1>Election Web Service</h1><p>This server only responds to posts. Try sending something like this:</p><code>curl -d \'{"voting_system": "stv", "ballots": [{"count": 4, "ballot": ["orange"]}, {"count": 2, "ballot": ["pear", "orange"]}, {"count": 8, "ballot": ["chocolate", "strawberry"]}, {"count": 4, "ballot": ["chocolate", "sweets"]}, {"count": 1, "ballot": ["strawberry"]}, {"count": 1, "ballot": ["sweets"]}], "winners": 3}\' http://vote.cognitivesandbox.com; echo;</code><p>For further documentation, see <a href="http://github.com/bradbeattie/Election-Web-Service">the GitHub project page</a>.</p></body></html>'
        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.send_header("Content-length", str(len(response)))
        self.end_headers()
        self.wfile.write(response)


    def do_POST(self):
        try:
            # Parse the incoming data
            jsonData = json.loads(self.rfile.read(int(self.headers["content-length"])))
            
            # Assume we're looking for a single winner
            if "winners" not in jsonData:
                jsonData["winners"] = 1
                
            # Assume each ballot represents a single voter's preference
            newInput = []
            for ballot in jsonData["ballots"]:
                if type(ballot) is not types.DictType:
                    ballot = {"ballot":ballot}
                if "count" not in ballot:
                    ballot["count"] = 1
                newInput.append(ballot)
            jsonData["ballots"] = newInput           

            # Send the data to the requested voting system
            if jsonData["voting_system"] in ["plurality", "fptp"]:
                response = Plurality.calculate_winner(jsonData["ballots"])
            elif jsonData["voting_system"] in ["pluralityAtLarge", "blockVoting"]:
                response = PluralityAtLarge.calculate_winner(jsonData["ballots"], jsonData["winners"])
            elif jsonData["voting_system"] in ["irv", "instantRunoff"]:
                response = IRV.calculate_winner(jsonData["ballots"], jsonData["winners"])
            elif jsonData["voting_system"] in ["stv", "singleTransferableVote"]:
                response = STV.calculate_winner(jsonData["ballots"], jsonData["winners"])
            elif jsonData["voting_system"] in ["rankedPairs", "tideman"]:
                response = RankedPairs.calculate_winner(jsonData["ballots"])
            elif jsonData["voting_system"] in ["schulzeMethod"]:
                response = SchulzeMethod.calculate_winner(jsonData["ballots"])
            elif jsonData["voting_system"] in ["schulzeSTV"]:
                raise Exception("Not yet implemented")
            else:
                raise
            
            # Ensure a response came back from the voting system
            if response == None:
                raise Exception("No voting system specified")
        except:
            fp = StringIO.StringIO()
            traceback.print_exc(10,fp)
            response = fp.getvalue()
            self.send_response(500)

        else:
            self.send_response(200)
            
        finally:
            response = json.dumps(self.__simplify_object__(response))
            self.send_header("Content-type", "application/json")
            self.send_header("Content-length", str(len(response)))
            self.end_headers()
            self.wfile.write(response)


    # json.dump() has a difficult time with certain object types
    def __simplify_object__(self, object):
        if type(object) == types.DictType:
            newDict = {}
            for key in object.keys():
                value = self.__simplify_object__(object[key])
                key = self.__simplify_object__(key)
                newDict[key] = value
            return newDict
        elif type(object) == types.TupleType:
            return "|".join(object)
        elif type(object) == type(set()) or type(object) == types.ListType:
            newList = []
            for element in object:
                newList.append(self.__simplify_object__(element))
            return newList
        else:
            return object

def main():
    try:
        server = HTTPServer(('', 8044), ElectionRequestHandler)
        print('Webservice running...')
        server.serve_forever()
    except KeyboardInterrupt:
        print('Webservice stopping...')
        server.socket.close()

if __name__ == '__main__':
    main()
