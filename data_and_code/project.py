import glob
import xml.etree.ElementTree as et
import os
import networkx as nx
from collections import Counter

#Question for Quentin - why are deputes seemingly being associated with parties that they aren't part of? Eg Jérémie Iordanoff, PA794022,
#is an ecologiste but in the other parties list it seems he is also associated with Libertés, Indépendants, Outre-mer et Territoires and
#Non inscrit

#use glob to get xml files. store as variable paths
bills = glob.glob("scrutins_XVI.xml/*")
orgs = glob.glob("acteurs_mandats_organes.xml/organe/*")

link = r"{http://schemas.assemblee-nationale.fr/referentiel}"

#Just some code to count how many instances of each code there are under the type vote child across the whole dataset, and see how this relates
#to the named type of vote

#code_votes = []
#type_votes = []
#
#for bill in bills:
#    tree = et.parse(bill)
#    root = tree.getroot()
#    code_votes.append(root.find(f".//{link}codeTypeVote").text)
#    type_votes.append(root.find(f".//{link}libelleTypeVote").text)
#
#print(pd.DataFrame(code_votes).value_counts())
#print(pd.DataFrame(type_votes).value_counts())

#the bills_2023 list contains only bills from 2023
bills_session = []

for bill in bills:
    tree = et.parse(bill)
    root = tree.getroot()
    if int(root.find(f"{link}dateScrutin").text[:4] + root.find(f"{link}dateScrutin").text[5:7]) >= 202308 and int(root.find(f"{link}dateScrutin").text[:4] + root.find(f"{link}dateScrutin").text[5:7]) <= 202406: #CHANGE THE 400 BACK TO 144  (or maybe 0?)
        bills_session.append(bill)

print("number bills: ", len(bills_session))

G = nx.Graph()

#function to add edges between all items in a list with an attribute with a weight of one, 
#or if an edge already exists increase that attribute's weight by one
def edge_adder(l, attr):
    for item in l:
        for next_item in l:
            if l.index(item) < l.index(next_item): #to avoid doubling up on edges eg item_a - item_b and item_b - item_a
                if not G.has_edge(item, next_item):
                    G.add_edge(item, next_item)
                    G[item][next_item][attr] = 1
                else:
                    if attr not in G[item][next_item].keys():
                        G[item][next_item][attr] = 1
                    else:
                        G[item][next_item][attr] += 1

bills_count = 0
#the for loop to end all for loops
for bill in bills_session:

    root_bill = et.parse(bill).getroot()

    ayes_ids = []
    noes_ids = []

    #going group by group
    group_roots = root_bill.findall(f".//{link}groupe")

    for group in group_roots:
        group_ref = group.find(f"{link}organeRef").text

        #getting all those voting 'for' and 'against'
        ayes_elements = group.findall(f".//{link}pours//{link}acteurRef")
        noes_elements = group.findall(f".//{link}contres//{link}acteurRef")
        
        #adding deputes from the current group to the ayes and noes list for this bill
        group_deps = []
        for aye in ayes_elements:
            group_deps.append(aye.text)
            ayes_ids.append(aye.text)
        for no in noes_elements:
            group_deps.append(no.text)
            noes_ids.append(no.text)

        for dep in group_deps: #for each group depute that voted on this bill
            root_party = et.parse(f"acteurs_mandats_organes.xml/organe/{group_ref}.xml").getroot()
            party_name = root_party.find(f".//{link}libelle").text
            if dep in G:
                #Checking if the depute switched parties. It seems that they are very few people who did, so for now we don't exclude
                #them and use their main party - by first getting a list of the party a depute was part of each time they voted
                G.nodes[dep]["parties"].append(party_name)
            else: #adding new deputes as nodes with their party and name as attributes
                root_dep = et.parse(f"acteurs_mandats_organes.xml/acteur/{dep}.xml").getroot()
                name = root_dep.find(f".//{link}prenom").text + " " + root_dep.find(f".//{link}nom").text
                party = [party_name]
                G.add_node(dep, parties = party, name = name)

    #adding edges between deputes that voted on the bill / increasing their edge's both_vote attribute
    all_voter_ids = ayes_ids + noes_ids
    edge_adder(all_voter_ids, "both_vote")

    #adding edges between deputes that voted the same way on the bill / increasing their edge's co_vote attribute
    edge_adder(ayes_ids, "co_vote")
    edge_adder(noes_ids, "co_vote")

    bills_count += 1
    print("bills processed: ", bills_count, "/", len(bills_session))

#adding the party that a depute voted with the most as their main party attribute
for dep in list(G):
    max_value = 0
    for key, value in Counter(G.nodes[dep]["parties"]).items(): #counts number of times a depute voted as a member of each party
            if value > max_value:
                max_value = value
                most_freq_key = key
    G.nodes[dep]["main_party"] = most_freq_key

#deleting node attribute that list all parties a depute was part of
for node in G:
    del G.nodes[node]["parties"] 

#calculating proportion of times deputes voted the same way on a bill, out of the number of times they both voted on a bill
for dep1, dep2, attrs in G.edges.data():
    G[dep1][dep2]["prop_covote"] = attrs.get("co_vote", 0)/attrs.get("both_vote") #the , 0 assigns the value of co_vote to 0 if it doesn't already exist

#removing edges with a prop co-vote weighting of 0. sadly cannot do that in prev loop as it affects the length of G.edges.data()
#edges_to_remove = [(n1, n2) for n1, n2, attrs in G.edges.data() if attrs.get("prop_covote")==0]
#G.remove_edges_from(edges_to_remove)

print(len(G.nodes))  #erm, slighty concerning that the number of nodes is 589 even though there are 577 deputes in the assemblee -
                     #but turns out there were 7 by-elections in 2023, so 7 old deputes and 7 new ones, meaning a total of 591 deputes
                     #could have voted in 2023. maybe I should remove deputes from the analysis who weren't there the whole year?

print(len(G.edges))

nx.write_gexf(G, "network_23_24.gexf")

#only 470 bills in 2021/2022?