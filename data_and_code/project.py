import glob
import xml.etree.ElementTree as et
import os
import networkx as nx

#Question for Quentin - why are deputes seemingly being associated with parties that they aren't part of? Eg Jérémie Iordanoff, PA794022,
#is an ecologiste but in the other parties list it seems he is also associated with Libertés, Indépendants, Outre-mer et Territoires and
#Non inscrit

#use glob to get xml files. store as variable paths
bills = glob.glob("scrutins.xml/*")
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

#the bills_2023_25pc list contains only bills from 2023 where at least 25% of deputes voted: 776 out of 4106 bills voted on 
#in the whole year
bills_2023_25pc = []

for bill in bills:
    tree = et.parse(bill)
    root = tree.getroot()
    if int(root.find(f".//{link}nombreVotants").text) >= 400 and root.find(f"{link}dateScrutin").text[:4] == "2023": #CHANGE THE 400 BACK TO 144
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

    #tree_bill = et.parse(bill)
    root_bill = et.parse(bill).getroot()

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
        #adding new deputes as nodes with their party and name as attributes
        deps = []
        for aye in ayes_elements:
            deps.append(aye.text)
            ayes_ids.append(aye.text)
        for no in noes_elements:
            deps.append(no.text)
            noes_ids.append(no.text)

        for dep in deps: #for each depute that voted on this bill
            root_party = et.parse(f"acteurs_mandats_organes.xml/organe/{group_ref}.xml").getroot()
            party_name = root_party.find(f".//{link}libelle").text
            if dep in G:
                #checking if the depute switched parties. It seems that they are very few people who did,
                # so for now we don't exclude them and use their main party
                if party_name not in G.nodes[dep]["parties"]:
                    G.nodes[dep]["parties"].append(party_name)
            else: #adding new deputes
                root_dep = et.parse(f"acteurs_mandats_organes.xml/acteur/{dep}.xml").getroot()
                name = root_dep.find(f".//{link}prenom").text + " " + root_dep.find(f".//{link}nom").text
                party = [party_name]
                G.add_node(dep, parties = party, name = name)
 
    #adding edges between deputes that voted the same way on the bill
    edge_adder(ayes_ids)
    edge_adder(noes_ids)

print(list(set(nx.get_node_attributes(G, "party").values()))) #getting a list of the parties

print(len(G.nodes))  #erm, slighty concerning that the number of nodes is 589 even though there are 577 deputes in the assemblee -
                     #but turns out there were 7 by-elections in 2023, so 7 old deputes and 7 new ones, meaning a total of 591 deputes
                     #could have voted in 2023. maybe I should remove deputes from the analysis who weren't there the whole year?

print(len(G.edges))

Jio = [aid for aid, at in G.nodes(data = True) if at["name"] == 'Jiovanny William']
Jer = [aid for aid, at in G.nodes(data = True) if at["name"] == 'Jérémie Iordanoff']
Lis = [aid for aid, at in G.nodes(data = True) if at["name"] == 'Lisa Belluco']

print("Jiovanny William: ", Jio)
print("Parties ", G.nodes[Jio[0]]["parties"])
print("Jérémie Iordanoff: ", Jer)
print("Parties ", G.nodes[Jer[0]]["parties"])
print("Lisa Belluco: ", Lis)
print("Parties ", G.nodes[Lis[0]]["parties"])
