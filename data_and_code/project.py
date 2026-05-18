import glob
import xml.etree.ElementTree as et
import os
import pandas as pd
import networkx as nx

os.chdir(r"c:/Users/lily_/OneDrive/Documents/Masters/S2/Computational_Social_Science/comp_soc_sci/data_and_code")

#use glob to get xml files. store as variable paths
bills = glob.glob("scrutins.xml/*")

link = r"{http://schemas.assemblee-nationale.fr/referentiel}" #Question for Quentin - why is there this link before the child name every time?

#Just some code to count how many instances of each code there are under the type vote child across the whole dataset, and see how this relates to the named type of vote

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

#the bills_2023_25pc list contains only bills from 2023 where at least 25% of deputes voted: 776 out of 4106 bills voted on 
#in the whole year
bills_2023_25pc = []

for bill in bills:
    tree = et.parse(bill)
    root = tree.getroot()
    if int(root.find(f".//{link}nombreVotants").text) >= 144 and root.find(f"{link}dateScrutin").text[:4] == "2023":
        bills_2023_25pc.append(bill)

G = nx.Graph()

#function to add edges between all items in a list with a weight of one, or if an edge already exists increase the weight by one
def edge_adder(l):
    for item in l:
        for next_item in l:
            if l.index(item) < l.index(next_item): #to avoid doubling up on edges eg item_a - item_b and item_b - item_a
                if not G.has_edge(item, next_item):
                    G.add_edge(item, next_item, weight = 1)
                else:
                    G[item][next_item]["weight"] += 1

#the for loop to end all for loops
for bill in bills_2023_25pc:

    tree_bill = et.parse(bill)
    root_bill = tree_bill.getroot()

    ayes_ids = []
    noes_ids = []

    #going group by group
    group_roots = root_bill.findall(f".//{link}groupe")

    for group in group_roots:
        group_ref = group.find(f"{link}organeRef").text

        #getting all those voting 'for' and 'against
        ayes_elements = group.findall(f".//{link}pours//{link}acteurRef")
        noes_elements = group.findall(f".//{link}contres//{link}acteurRef")

        #adding deputes to the ayes and noes list for this bill
        for aye in ayes_elements:
            ayes_ids.append(aye.text)

        for no in noes_elements:
            noes_ids.append(no.text)

        #adding new deputes as nodes with their party reference as an attribute
        deps = ayes_ids + noes_ids
        for dep in deps: #could probably add name attribute here
            if dep not in G:
                G.add_node(dep, party = group_ref)
 
    #adding edges between deputes that voted the same way on the bill
    edge_adder(ayes_ids)
    edge_adder(noes_ids)


print(nx.get_node_attributes(G, "party"))

print(len(G.nodes))  #erm, slighty concerning that the number of nodes is 589 even though there are 577 deputes in the assemblee -
                     #but turns out there were 7 by-elections in 2023, so 7 old deputes and 7 new ones, meaning a total of 591 deputes
                     #could have voted in 2023. maybe I should remove deputes from the analysis who weren't there the whole year?

print(len(G.edges))

