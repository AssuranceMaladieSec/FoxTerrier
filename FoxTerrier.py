#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Author : Alice Climent-Pommeret (Pentester @ Caisse Nationale de l'Assurance Maladie)
# Copyright (c) Caisse nationale d'Assurance Maladie
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, version 3 of the License.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

from neo4j import GraphDatabase
import json
import csv
from os import path
import configparser

class FoxTerrier:

    def __init__(self, uri, user, password):
        self.driver = GraphDatabase.driver(uri, auth=(user, password))
        self.stats_per_node = {}
        self.stats_per_node_RDP = {}
        self.stats_per_objects = {}

    def close(self):
        self.driver.close()
        
        
    def load_json(self,myfile, synthesis_file):
        items_list = []
        # Opening JSON file
        with open(myfile, "r") as in_file:
            # returns JSON object as a dictionary
            data = json.load(in_file)
            
        loaded_file_str = f"--- Load JSON File {myfile}"
        
        self.write_synthesis_file(synthesis_file, "")
        self.write_synthesis_file(synthesis_file, loaded_file_str)
        # Iterating through the json
        # Set data to construct the queries in a list of dictionnaries
        for item in data['queries']:
            res = {}
            #The node start type must be "User" or "Group"
            res["node_start_type"] = item.get("node_start_type", None)  
            
            if not res["node_start_type"]:
                print("")
                print("ERROR :")
                print("node_start_type missing !")
                print("")
                exit(1)
            
            #The full name of a node start or a regex
            res["node_start_name"] = item.get("node_start_name", None)
            if not res["node_start_name"]:
                print("")
                print("ERROR :")
                print("node_start_name missing !")
                print("")
                exit(1)
            
            #If node start name is a regex this value must be set to true (default value false)
            res["is_node_start_regex"] = item.get("is_node_start_regex", False)
            
            #The mode can be "direct" for direct relationship "indirect" for indirect relationship
            #If you want both "direct"+"indirect", you can set "all" (default value "direct")
            res["mode"] = item.get("mode", "direct")
            
            #If you want to exclude node set them in the list ["node1","node2"] (default value [])
            res["exclude_node"] = item.get("exclude_node", [])
        
            #The target object you want to highlight the relationship with
            #Can be "GPO", "OU" ,"User", "Group", "RDP" (RDP is for the CanRDP relation)
            #The object as to be in a list (example : ["GPO","User"] )
            # Default value ["GPO", "OU" ,"User", "Group", "RDP"]
            res["objects_type"] = item.get("objects_type", None)
            if not res["objects_type"]:
                res["objects_type"] = ["GPO", "OU" ,"User", "Group", "RDP"]
      
            items_list.append(res)

        print(f"--- JSON file {myfile} Loaded ---")
        print("")
        return items_list
        

        
    def format_items(self, items_list):
        
        for item in items_list:
            if item["node_start_type"].lower() == "group":
                item["node_start_type"] = "Group"
            elif item["node_start_type"].lower() == "user":
                item["node_start_type"] = "User"
            else:
                print('Invalid node start type. Type must be "User" or "Group"')
                exit(1)
            
            if item["mode"].lower() == "direct":
                item["mode"] = "direct"
            elif item["mode"].lower() == "indirect":
                item["mode"] = "indirect"
            elif item["mode"].lower() == "all":
                item["mode"] = "all"
            else:
                print('Invalid mode. Mode must be "direct" or "indirect" or "all"')
                exit(1)             
                
            if not isinstance(item["is_node_start_regex"], bool):
                print('Invalid is_node_start_regex value. Must be true or false (without quote or double quote) ')
                exit(1)
            type_list=[]

            for obj_type in item["objects_type"]:
                if (obj_type.lower() == "ou") or  (obj_type.lower() == "gpo"):
                    type_list.append(obj_type.upper())
                elif (obj_type.lower() == "user") or  (obj_type.lower() == "group"): 
                    type_list.append(obj_type.lower().capitalize())
                elif (obj_type.lower() == "rdp"):
                    type_list.append("CanRDP")       
                else:
                    print('Invalid Objects Type. Object Type must be "GPO" or "OU" or "User" or "Group" or "RDP"')
                    exit(1)
                                        
            item["objects_type"] = type_list
        return items_list
        
    def create_queries(self, items_list):
        queries = []
        for item in items_list:
            
            query = []
            node_start_type = item['node_start_type']
            
            #For each object in the json file prepare a specific request
            for obj_type in item["objects_type"]:                    
                node_start = item['node_start_name']

                if item['is_node_start_regex']:
                    symbol = "=~"
                else:
                    symbol = "="

                query_exclude = " ".join([f"AND NOT m.name = '{i}'" for i in item['exclude_node']])
                
                query_dir = f"Match p=(m:{node_start_type})-[r]->(n:{obj_type}) WHERE m.name {symbol} '{node_start}' {query_exclude} and r.isacl=true return m.name AS start_name, n.name AS end_name, n.distinguishedname AS end_distinguishedname"
                query_indir = f"Match p=(m:{node_start_type})-[r1:MemberOf*1..]->(g2:Group)-[r2]->(n:{obj_type}) WHERE m.name {symbol} '{node_start}' {query_exclude} and r2.isacl=true return m.name AS start_name, n.name AS end_name, n.distinguishedname AS end_distinguishedname"
                query_dir_RDP = f"Match p=(m:{node_start_type})-[r:{obj_type}]->(n:Computer) WHERE m.name {symbol} '{node_start}' {query_exclude} return m.name AS start_name, n.name AS end_name, n.distinguishedname AS end_distinguishedname"
                query_indir_RDP = f"Match p=(m:{node_start_type})-[r1:MemberOf*1..]->(g2:Group)-[r2:{obj_type}]->(n:Computer) WHERE m.name {symbol} '{node_start}' {query_exclude} return m.name AS start_name, n.name AS end_name, n.distinguishedname AS end_distinguishedname"
                
                
                #Prepare query for not "all" mode
                if obj_type != "CanRDP" :                   
                    if item['mode'].lower() == "direct":               
                        query = query_dir           
                    elif item['mode'].lower() == "indirect":
                        query = query_indir
                else:
                    if item['mode'].lower() == "direct":
                        query = query_dir_RDP 
                    elif item['mode'].lower() == "indirect":
                        query = query_indir_RDP
         
                    
                if item['mode'].lower() != "all":
                    to_add = [query, obj_type]
                    queries.append(to_add)
                #Prepare query for "all" mode
                else:
                    if obj_type != "CanRDP" :
                        to_add = [query_dir, obj_type]
                        queries.append(to_add)
                        to_add = [query_indir, obj_type]
                        queries.append(to_add)
                    else:
                        to_add = [query_dir_RDP, obj_type]
                        queries.append(to_add)
                        to_add = [query_indir_RDP, obj_type]
                        queries.append(to_add) 
                        
        return queries
        
       

    def execute_queries(self, queries, synthesis_file):
        result = []
        with self.driver.session() as session:
            self.stats_per_node = {}
            self.stats_per_node_RDP = {}
            self.stats_per_objects = {}
            
            self.write_synthesis_file(synthesis_file, "")
            self.write_synthesis_file(synthesis_file, "--- Executed queries ---")
            for query in queries:

                the_query = query[0]
                object_type = query[1]

                self.write_synthesis_file(synthesis_file, the_query)
                self.write_synthesis_file(synthesis_file, "")

                graph = session.run(the_query)
                
                for res in graph:   
                    line= [f"{res['start_name']}",
                           f"{res['end_name']}",
                           f"{res['end_distinguishedname']}",
                           f"{object_type}"]
                    result.append(line)
                    
                    if object_type != "CanRDP":
                        if not res['start_name'] in self.stats_per_node:
                            self.stats_per_node[res['start_name']] = 1
                    else:
                        if not res['start_name'] in self.stats_per_node_RDP:
                            self.stats_per_node_RDP[res['start_name']] = 1
                            
                    if not object_type in self.stats_per_objects:
                        self.stats_per_objects[object_type] = 1
                    
      
            results = [list(x) for x in set(tuple(x) for x in result)]
            self.summary_results(results, synthesis_file)
            return results

    def summary_results(self, results, synthesis_file):
        
        for elem in self.stats_per_node:
            self.stats_per_node[elem] = sum([1 for s in results if elem == s[0] and s[3] != "CanRDP"])

        for elem in self.stats_per_node_RDP:
            self.stats_per_node_RDP[elem] = sum([1 for s in results if elem == s[0] and s[3] == "CanRDP"])
            
        for elem in self.stats_per_objects:
            self.stats_per_objects[elem] = sum(elem == s[3] for s in results)
        self.write_synthesis_file(synthesis_file, "--- Summary of vulnerable object per User or Group ---")
        self.write_synthesis_file(synthesis_file, "")
        
        for elem in self.stats_per_node : 
            mystring = f"{elem} : {self.stats_per_node[elem]}"
            self.write_synthesis_file(synthesis_file, mystring)


        self.write_synthesis_file(synthesis_file, "")
        self.write_synthesis_file(synthesis_file, "--- Summary of CanRDP machines per User or Group ---")
        self.write_synthesis_file(synthesis_file, "")
        for elem in self.stats_per_node_RDP : 
            mystring = f"{elem} : {self.stats_per_node_RDP[elem]}"
            self.write_synthesis_file(synthesis_file, mystring)
            
        
        self.write_synthesis_file(synthesis_file, "")
        self.write_synthesis_file(synthesis_file, "--- Summary of vulnerable object per Type ---")
        self.write_synthesis_file(synthesis_file, "")
        for elem in self.stats_per_objects: 
            mystring = f"{elem} : {self.stats_per_objects[elem]}"
            self.write_synthesis_file(synthesis_file, mystring)
 
        
    def write_results(self,results, output_file, synthesis_file):
        
        with open(output_file, 'w', newline='') as f:
            header = ['Start Object', 'Vulnerable Object','Distinguished Name Vulnerable Object', 'Type'] 
            write = csv.writer(f, delimiter=";")
            write.writerow(header)
            write.writerows(results)
        

        mystring = f"--- Results available in {output_file} ---"

        self.write_synthesis_file(synthesis_file, "")
        self.write_synthesis_file(synthesis_file, mystring)
        self.write_synthesis_file(synthesis_file, "")

        
    def generate(self, my_template_file, output_file, synthesis_file):
        if not path.exists(my_template_file):
            print("")
            print(f"The template file {my_template_file} doesn't exist")
            print("")
            exit(1)
        
        if path.exists(output_file):
            print("")
            print(f"The output file {output_file} already exist")
            print("")
            exit(1)
        
        if path.exists(synthesis_file):
            print("")
            print(f"The synthesis file {synthesis_file} already exist")
            print("")
            exit(1) 
            
        items_list = self.load_json(my_template_file, synthesis_file)
        formated_items_list = self.format_items(items_list)
        created_queries = self.create_queries(formated_items_list)
        resultats = self.execute_queries(created_queries, synthesis_file)
        self.write_results(resultats, output_file, synthesis_file)
    
    def write_synthesis_file(self, synthesis_file, line):
        print(line)
        with open(synthesis_file, "a") as fs:
            fs.write(f"{line}\n")
        
    
if __name__ == "__main__":
    
    config = configparser.RawConfigParser()
    config.read('./conf.ini')
    neo4jaddress = config['neo4j_credentials']['address']
    neo4jport = config['neo4j_credentials']['port']
    user = config['neo4j_credentials']['username']
    password = config['neo4j_credentials']['password']
    connexion_url = f"bolt://{neo4jaddress}:{neo4jport}"

    
    my_template_file = f"./{config['files']['template_file']}"
    output_file = f"./{config['files']['csv_report']}"
    synthesis_file = f"./{config['files']['txt_summary']}"
    
    blanqui = FoxTerrier(connexion_url, user, password)
    blanqui.generate(my_template_file, output_file, synthesis_file)
    blanqui.close()
