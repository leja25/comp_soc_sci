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

#the bills_2023_25pc list contains only bills from 2023 where at least 25% of deputes voted: 776 out of 4106 bills voted on in the whole year

bills_2023_25pc = []

for bill in bills:
    tree = et.parse(bill)
    root = tree.getroot()
    if int(root.find(f".//{link}nombreVotants").text) >= 144 and root.find(f"{link}dateScrutin").text[:4] == "2023":
        bills_2023_25pc.append(bill)

G = nx.Graph()

#the for loop to end all for loops
for bill in bills_2023_25pc:

    tree = et.parse(bill)
    root = tree.getroot()

    #getting all those voting 'for'
    ayes_id = []
    ayes_elements = root.findall(f".//{link}pours/{link}votant/{link}acteurRef")

    for aye in ayes_elements:
        ayes_id.append(aye.text)
    
    #adding them as a node if they haven't already been added
    for aye in ayes_id:
        if aye not in G:
            G.add_node(aye)

    #getting all those voting 'against'
    noes_id = []
    noes_elements = root.findall(f".//{link}contres/{link}votant/{link}acteurRef")
    for noe in noes_elements:
        noes_id.append(noe.text)

    #adding them as a node if they haven't already been added
    for noe in noes_id:
        if noe not in G:
            G.add_node(noe)

print(len(G.nodes))  #erm, slighty concerning that the number of nodes is 589 even though there are 577 deputes in the assemblee -
                     #but turns out there were 7 by-elections in 2023, so 7 old deputes and 7 new ones, meaning a total of 591
                     #deputes could have voted in 2023. maybe I should remove depute from the analysis who weren't there the whole year?