# Galileo → Open‑PSA Converter

A lightweight/minimal PoC Python tool to convert **GALILEO** Fault Tree models (*.gal) into **Open‑PSA MEF** XML (*.xml) that validate against the official schema.

## 📁 Repository Structure

.
├── gal2opsa.py        # main conversion script
├── mef.xsd            # Open‑PSA XML Schema
└── examples/
    ├── baobab.gal
    ├── baobab.xml
    ├── edf9203.gal
    ├── edf9203.xml
    ├── nus9601.gal
    └── nus9601.xml

## 🚀 Usage

Convert a .gal file to .xml:

```bash
python3 gal2opsa.py examples/edf9203.gal examples/edf9203.xml
```

## ✅ Schema Validation

Check that the generated XML complies with the MEF schema using:

```bash
xmllint --noout --schema mef.xsd examples/edf9203.xml
```

The MEF schema is maintained by the official Open‑PSA project and defines the structure for Model Exchange Format version 2.0.d:

[Open‑PSA MEF Schema (mef.xsd)](https://github.com/open-psa/schemas/blob/master/2.0d/mef.xsd)

## 🛠️ Dependencies

- **Python 3**  
- **lxml** (install via `pip install lxml`)  
- **xmllint** (from `libxml2`) for schema validation


