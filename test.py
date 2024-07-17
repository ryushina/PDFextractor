import json
import os
import re


def main():
    fields = """
   [
    {
        "Asset Name": "Aix-En-Provence",
        "Filename": "filename_of_pdf.pdf",
        "Delivery Date": null,
        "City": null,
        "Country": null,
        "Start of Lease": "Jul-20",
        "Lease Duration in Years": 7.8,
        "Seller": null,
        "Tenant": "Perrenot Vitrolles",
        "GLA (Gross Leasable Area)": 3780,
        "IP-Rent": 532849,
        "Start of Contract": null
    },
    {
        "Asset Name": "Athies",
        "Filename": "filename_of_pdf.pdf",
        "Delivery Date": null,
        "City": null,
        "Country": null,
        "Start of Lease": "Jul-20",
        "Lease Duration in Years": 7.8,
        "Seller": null,
        "Tenant": "Perrenot Bekaert",
        "GLA (Gross Leasable Area)": 6067,
        "IP-Rent": 434692,
        "Start of Contract": null
    },
    {
        "Asset Name": "Béziers",
        "Filename": "filename_of_pdf.pdf",
        "Delivery Date": null,
        "City": null,
        "Country": null,
        "Start of Lease": "Jul-20",
        "Lease Duration in Years": 7.8,
        "Seller": null,
        "Tenant": "Perrenot Buchaca",
        "GLA (Gross Leasable Area)": 1900,
        "IP-Rent": 350558,
        "Start of Contract": null
    },
    {
        "Asset Name": "Châtenois",
        "Filename": "filename_of_pdf.pdf",
        "Delivery Date": null,
        "City": null,
        "Country": null,
        "Start of Lease": "Jul-22",
        "Lease Duration in Years": 12.8,
        "Seller": null,
        "Tenant": "Perrenot Transvallées",
        "GLA (Gross Leasable Area)": 13389,
        "IP-Rent": 536735,
        "Start of Contract": null
    },
    {
        "Asset Name": "Cholet",
        "Filename": "filename_of_pdf.pdf",
        "Delivery Date": null,
        "City": null,
        "Country": null,
        "Start of Lease": "Jan-23",
        "Lease Duration in Years": 10.3,
        "Seller": null,
        "Tenant": "Perrenot Le Calvez Surgelés",
        "GLA (Gross Leasable Area)": 3244,
        "IP-Rent": 467348,
        "Start of Contract": null
    },
    {
        "Asset Name": "Cournon-D'Auvergne",
        "Filename": "filename_of_pdf.pdf",
        "Delivery Date": null,
        "City": null,
        "Country": null,
        "Start of Lease": "Jul-20",
        "Lease Duration in Years": 5.8,
        "Seller": null,
        "Tenant": "Perrenot Auvergne",
        "GLA (Gross Leasable Area)": 1573,
        "IP-Rent": 210335,
        "Start of Contract": null
    },
    {
        "Asset Name": "Escrennes",
        "Filename": "filename_of_pdf.pdf",
        "Delivery Date": null,
        "City": null,
        "Country": null,
        "Start of Lease": "Jan-22",
        "Lease Duration in Years": 12.3,
        "Seller": null,
        "Tenant": "Perrenot Pithiviers",
        "GLA (Gross Leasable Area)": 1083,
        "IP-Rent": 269671,
        "Start of Contract": null
    },
    {
        "Asset Name": "Heudebouville",
        "Filename": "filename_of_pdf.pdf",
        "Delivery Date": null,
        "City": null,
        "Country": null,
        "Start of Lease": "Jul-20",
        "Lease Duration in Years": 7.8,
        "Seller": null,
        "Tenant": "Perrenot Normandie",
        "GLA (Gross Leasable Area)": 2400,
        "IP-Rent": 303817,
        "Start of Contract": null
    },
    {
        "Asset Name": "Jonage",
        "Filename": "filename_of_pdf.pdf",
        "Delivery Date": null,
        "City": null,
        "Country": null,
        "Start of Lease": "Jul-20",
        "Lease Duration in Years": 7.8,
        "Seller": null,
        "Tenant": "Perrenot Jonage",
        "GLA (Gross Leasable Area)": 5021,
        "IP-Rent": 654375,
        "Start of Contract": null
    },
    {
        "Asset Name": "Les Sorinières",
        "Filename": "filename_of_pdf.pdf",
        "Delivery Date": null,
        "City": null,
        "Country": null,
        "Start of Lease": "Jul-20",
        "Lease Duration in Years": 7.8,
        "Seller": null,
        "Tenant": "Perrenot Nantes",
        "GLA (Gross Leasable Area)": 2631,
        "IP-Rent": 373929,
        "Start of Contract": null
    },
    {
        "Asset Name": "Marolles-sur-Seine",
        "Filename": "filename_of_pdf.pdf",
        "Delivery Date": null,
        "City": null,
        "Country": null,
        "Start of Lease": "Jul-20",
        "Lease Duration in Years": 5.8,
        "Seller": null,
        "Tenant": "Perrenot Solutions",
        "GLA (Gross Leasable Area)": 8748,
        "IP-Rent": 584264,
        "Start of Contract": null
    },
    {
        "Asset Name": "Migné-Auxances",
        "Filename": "filename_of_pdf.pdf",
        "Delivery Date": null,
        "City": null,
        "Country": null,
        "Start of Lease": "Jul-20",
        "Lease Duration in Years": 7.8,
        "Seller": null,
        "Tenant": "Perrenot Hersand",
        "GLA (Gross Leasable Area)": 4852,
        "IP-Rent": 501363,
        "Start of Contract": null
    },
    {
        "Asset Name": "Miramas",
        "Filename": "filename_of_pdf.pdf",
        "Delivery Date": null,
        "City": null,
        "Country": null,
        "Start of Lease": "Jul-20",
        "Lease Duration in Years": 7.8,
        "Seller": null,
        "Tenant": "Perrenot Salon de Provence",
        "GLA (Gross Leasable Area)": 1011,
        "IP-Rent": 175279,
        "Start of Contract": null
    },
    {
        "Asset Name": "Montbartier",
        "Filename": "filename_of_pdf.pdf",
        "Delivery Date": null,
        "City": null,
        "Country": null,
        "Start of Lease": "Jan-22",
        "Lease Duration in Years": 12.3,
        "Seller": null,
        "Tenant": "Perrenot Le Calvez Surgelés",
        "GLA (Gross Leasable Area)": 6950,
        "IP-Rent": 1186552,
        "Start of Contract": null
    },
    {
        "Asset Name": "Noyal-sur-Vilaine",
        "Filename": "filename_of_pdf.pdf",
        "Delivery Date": null,
        "City": null,
        "Country": null,
        "Start of Lease": "Dec-20",
        "Lease Duration in Years": 8.2,
        "Seller": null,
        "Tenant": "Perrenot Le Calvez Surgelés",
        "GLA (Gross Leasable Area)": 10729,
        "IP-Rent": 988398,
        "Start of Contract": null
    },
    {
        "Asset Name": "Saint-Denis-lès-Bourgs",
        "Filename": "filename_of_pdf.pdf",
        "Delivery Date": null,
        "City": null,
        "Country": null,
        "Start of Lease": "Nov-22",
        "Lease Duration in Years": 13.1,
        "Seller": null,
        "Tenant": "La Fleche Bressane",
        "GLA (Gross Leasable Area)": 2750,
        "IP-Rent": 511269,
        "Start of Contract": null
    },
    {
        "Asset Name": "Valence",
        "Filename": "filename_of_pdf.pdf",
        "Delivery Date": null,
        "City": null,
        "Country": null,
        "Start of Lease": "Jul-20",
        "Lease Duration in Years": 7.8,
        "Seller": null,
        "Tenant": "Perrenot Vrac",
        "GLA (Gross Leasable Area)": 1121,
        "IP-Rent": 280447,
        "Start of Contract": null
    }
]
    """

    match = json.loads(fields)
    return match

def get_filename():
    file_path = ""
    for filename in os.listdir(input_dir):
        if filename.endswith(".pdf"):
            file_path = os.path.join(input_dir, filename)
    return file_path
             
   

if __name__ == "__main__":
    input_dir = './input'

    print(get_filename())
    print(type(get_filename()))
    result = main()


    #print(result)
