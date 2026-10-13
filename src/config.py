"""Paths, column mappings and constants shared by every pipeline step."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = ROOT / "data" / "raw"
PROCESSED_DIR = ROOT / "data" / "processed"
TABLES_DIR = ROOT / "outputs" / "tables"
CHARTS_DIR = ROOT / "outputs" / "charts"
TABLEAU_DIR = ROOT / "tableau"

RAW_FILE = RAW_DIR / "DataCoSupplyChainDataset.csv"
CLEAN_FILE = PROCESSED_DIR / "order_lines_clean.csv"
TABLEAU_FILE = TABLEAU_DIR / "tableau_order_lines.csv"

KAGGLE_URL = (
    "https://www.kaggle.com/api/v1/datasets/download/"
    "shashwatwork/dataco-smart-supply-chain-for-big-data-analysis"
)

# The raw file is not UTF-8: names like "México" only decode as latin-1.
RAW_ENCODING = "latin-1"

# Orders from Oct-2017 on have one line per order and far fewer categories,
# so monthly trends stop at the last full-shape month.
TREND_CUTOFF = "2017-10-01"

# Columns dropped before analysis, with the reason for each.
DROP_COLUMNS = {
    # Personal data, not needed and not safe to publish
    "Customer Email": "PII (masked but useless)",
    "Customer Password": "PII (masked but useless)",
    "Customer Fname": "PII",
    "Customer Lname": "PII",
    "Customer Street": "PII",
    # Empty or constant
    "Product Description": "100% null",
    "Order Zipcode": "86% null",
    "Product Status": "constant (always 0)",
    "Product Image": "URL, no analytical value",
    # Exact duplicates of another column (verified in clean.py)
    "Benefit per order": "duplicate of Order Profit Per Order",
    "Sales per customer": "duplicate of Order Item Total",
    "Order Item Cardprod Id": "duplicate of Product Card Id",
    "Product Category Id": "duplicate of Category Id",
    "Order Customer Id": "duplicate of Customer Id",
    "Order Item Product Price": "duplicate of Product Price",
}

DUPLICATE_PAIRS = [
    ("Benefit per order", "Order Profit Per Order"),
    ("Sales per customer", "Order Item Total"),
    ("Order Item Cardprod Id", "Product Card Id"),
    ("Product Category Id", "Category Id"),
    ("Order Customer Id", "Customer Id"),
    ("Order Item Product Price", "Product Price"),
]

RENAME = {
    "Type": "payment_type",
    "Days for shipping (real)": "days_real",
    "Days for shipment (scheduled)": "days_scheduled",
    "Delivery Status": "delivery_status",
    "Late_delivery_risk": "late_flag_source",
    "Category Id": "category_id",
    "Category Name": "category",
    "Customer City": "store_city",
    "Customer Country": "store_country",
    "Customer Id": "customer_id",
    "Customer Segment": "customer_segment",
    "Customer State": "store_state",
    "Customer Zipcode": "store_zipcode",
    "Department Id": "department_id",
    "Department Name": "department",
    "Latitude": "store_lat",
    "Longitude": "store_lon",
    "Market": "market",
    "Order City": "order_city",
    "Order Country": "order_country_es",
    "order date (DateOrders)": "order_date",
    "Order Id": "order_id",
    "Order Item Discount": "discount",
    "Order Item Discount Rate": "discount_rate",
    "Order Item Id": "order_item_id",
    "Order Item Profit Ratio": "profit_ratio",
    "Order Item Quantity": "quantity",
    "Sales": "gross_sales",
    "Order Item Total": "net_sales",
    "Order Profit Per Order": "profit",
    "Order Region": "order_region",
    "Order State": "order_state",
    "Order Status": "order_status",
    "Product Card Id": "product_id",
    "Product Name": "product",
    "Product Price": "unit_price",
    "shipping date (DateOrders)": "ship_date",
    "Shipping Mode": "shipping_mode",
}

SHIPPING_MODE_ORDER = ["Same Day", "First Class", "Second Class", "Standard Class"]

# Order Country is in Spanish; Tableau's geocoder needs English names.
COUNTRY_ES_TO_EN = {
    "Afganistán": "Afghanistan", "Albania": "Albania", "Alemania": "Germany",
    "Angola": "Angola", "Arabia Saudí": "Saudi Arabia", "Argelia": "Algeria",
    "Argentina": "Argentina", "Armenia": "Armenia", "Australia": "Australia",
    "Austria": "Austria", "Azerbaiyán": "Azerbaijan", "Bangladés": "Bangladesh",
    "Barbados": "Barbados", "Baréin": "Bahrain", "Belice": "Belize",
    "Benín": "Benin", "Bielorrusia": "Belarus", "Bolivia": "Bolivia",
    "Bosnia y Herzegovina": "Bosnia and Herzegovina", "Botsuana": "Botswana",
    "Brasil": "Brazil", "Bulgaria": "Bulgaria", "Burkina Faso": "Burkina Faso",
    "Burundi": "Burundi", "Bután": "Bhutan", "Bélgica": "Belgium",
    "Camboya": "Cambodia", "Camerún": "Cameroon", "Canada": "Canada",
    "Chad": "Chad", "Chile": "Chile", "China": "China", "Chipre": "Cyprus",
    "Colombia": "Colombia", "Corea del Sur": "South Korea",
    "Costa Rica": "Costa Rica", "Costa de Marfil": "Ivory Coast",
    "Croacia": "Croatia", "Cuba": "Cuba", "Dinamarca": "Denmark",
    "Ecuador": "Ecuador", "Egipto": "Egypt", "El Salvador": "El Salvador",
    "Emiratos Árabes Unidos": "United Arab Emirates", "Eritrea": "Eritrea",
    "Eslovaquia": "Slovakia", "Eslovenia": "Slovenia", "España": "Spain",
    "Estados Unidos": "United States", "Estonia": "Estonia",
    "Etiopía": "Ethiopia", "Filipinas": "Philippines", "Finlandia": "Finland",
    "Francia": "France", "Gabón": "Gabon", "Georgia": "Georgia",
    "Ghana": "Ghana", "Grecia": "Greece", "Guadalupe": "Guadeloupe",
    "Guatemala": "Guatemala", "Guayana Francesa": "French Guiana",
    "Guinea": "Guinea", "Guinea Ecuatorial": "Equatorial Guinea",
    "Guinea-Bissau": "Guinea-Bissau", "Guyana": "Guyana", "Haití": "Haiti",
    "Honduras": "Honduras", "Hong Kong": "Hong Kong", "Hungría": "Hungary",
    "India": "India", "Indonesia": "Indonesia", "Irak": "Iraq",
    "Irlanda": "Ireland", "Irán": "Iran", "Israel": "Israel", "Italia": "Italy",
    "Jamaica": "Jamaica", "Japón": "Japan", "Jordania": "Jordan",
    "Kazajistán": "Kazakhstan", "Kenia": "Kenya", "Kirguistán": "Kyrgyzstan",
    "Kuwait": "Kuwait", "Laos": "Laos", "Lesoto": "Lesotho",
    "Liberia": "Liberia", "Libia": "Libya", "Lituania": "Lithuania",
    "Luxemburgo": "Luxembourg", "Líbano": "Lebanon", "Macedonia": "North Macedonia",
    "Madagascar": "Madagascar", "Malasia": "Malaysia", "Mali": "Mali",
    "Marruecos": "Morocco", "Martinica": "Martinique", "Mauritania": "Mauritania",
    "Moldavia": "Moldova", "Mongolia": "Mongolia", "Montenegro": "Montenegro",
    "Mozambique": "Mozambique", "Myanmar (Birmania)": "Myanmar",
    "México": "Mexico", "Namibia": "Namibia", "Nepal": "Nepal",
    "Nicaragua": "Nicaragua", "Nigeria": "Nigeria", "Noruega": "Norway",
    "Nueva Zelanda": "New Zealand", "Níger": "Niger", "Omán": "Oman",
    "Pakistán": "Pakistan", "Panamá": "Panama",
    "Papúa Nueva Guinea": "Papua New Guinea", "Paraguay": "Paraguay",
    "Países Bajos": "Netherlands", "Perú": "Peru", "Polonia": "Poland",
    "Portugal": "Portugal", "Qatar": "Qatar", "Reino Unido": "United Kingdom",
    "República Centroafricana": "Central African Republic",
    "República Checa": "Czech Republic",
    "República Democrática del Congo": "Democratic Republic of the Congo",
    "República Dominicana": "Dominican Republic",
    "República de Gambia": "Gambia", "República del Congo": "Republic of the Congo",
    "Ruanda": "Rwanda", "Rumania": "Romania", "Rusia": "Russia",
    "Senegal": "Senegal", "Serbia": "Serbia", "Sierra Leona": "Sierra Leone",
    "Singapur": "Singapore", "Siria": "Syria", "Somalia": "Somalia",
    "Sri Lanka": "Sri Lanka", "Suazilandia": "Eswatini",
    "SudAfrica": "South Africa", "Sudán": "Sudan", "Sudán del Sur": "South Sudan",
    "Suecia": "Sweden", "Suiza": "Switzerland", "Surinam": "Suriname",
    "Sáhara Occidental": "Western Sahara", "Tailandia": "Thailand",
    "Taiwán": "Taiwan", "Tanzania": "Tanzania", "Tayikistán": "Tajikistan",
    "Togo": "Togo", "Trinidad y Tobago": "Trinidad and Tobago",
    "Turkmenistán": "Turkmenistan", "Turquía": "Turkey", "Túnez": "Tunisia",
    "Ucrania": "Ukraine", "Uganda": "Uganda", "Uruguay": "Uruguay",
    "Uzbekistán": "Uzbekistan", "Venezuela": "Venezuela", "Vietnam": "Vietnam",
    "Yemen": "Yemen", "Yibuti": "Djibouti", "Zambia": "Zambia",
    "Zimbabue": "Zimbabwe",
}

STORE_COUNTRY_FIX = {"EE. UU.": "United States"}
