import glob
import xml.etree.ElementTree as et
import os

os.chdir(r"c:/Users/lily_/OneDrive/Documents/Masters/S2/Computational_Social_Science/comp_soc_sci/data_and_code")
print(os.getcwd())

#use glob to get xml files. store as variable paths /*.xml
paths = glob.glob("scrutins.xml.zip/*")

print(paths)
#do a for loop for path in paths keep only laws where eg 20% of deputes voted (then see how many laws left. maybe adjust the percentage)