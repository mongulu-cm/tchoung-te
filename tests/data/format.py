import csv
from rich import print as pprint
categories = {}

with open('ref-association-code.csv', newline='') as csvfile:
    spamreader = csv.reader(csvfile)
    for row in spamreader:
        if "domaine_activite_categorise" in row:
            continue
        if len(row[0].split("/")) == 2:
            if row[0].split("/")[1] == "":
                categories[row[0].split("/")[0]] = row[1].split("/")[0]
            else:
                categories[row[0].split("/")[0]] = row[1].split("/")[0]
                categories[row[0].split("/")[1]] = row[1].split("/")[1]

        else:
            for i in range(0,len(row[0].split("###"))-1):
                if len(row[0].split("###")[i].split("/")) == 2:
                    if row[0].split("###")[i].split("/")[1] == "":
                        categories[row[0].split("###")[i].split("/")[0]] = row[1].split("###")[i].split("/")[0]
                    else:
                        categories[row[0].split("###")[i].split("/")[0]] = row[1].split("###")[i].split("/")[0]
                        categories[row[0].split("###")[i].split("/")[1]] = row[1].split("###")[i].split("/")[1]


pprint(categories)

# social_object1 / social_object2