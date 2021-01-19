**OneNode Md Export** is a console application running on Windows that exports your OneNote notebooks in different markdown formats. Currently, **Joplin markdown directory** and **Markdown directory** are supported.

The main objective of this repository is to offer to OneNote users the most simple and lossless solution to migrate to Joplin.
It offers an alternative to migration based on EverNote export (OneNote-> ENEX -> Joplin), in particular for people organizing their notes using hierarchy of sections and hierarchy of pages, lost during EverNote import.

Technical characteristics :
* DotNet 5 console application
* Load Notebook tree using Office Interop APIs
* Export page as DocX and translate them in Md (GitHub Flavor) using PanDoc
* Apply some post-processing based on Regex to correct some formatting issues
* Customizable : post-processing can be disabled in settings
* Extensible : new export format can be easily added to the code
* Offline : no request to Microsoft Graph API

# Requirements

Tested on : 
* Windows 10
* Office 2016
* Joplin 1.6

Please tell me if other versions work for you.

# User guide
## Installation

* Install DotNet 5 : https://dotnet.microsoft.com/download/dotnet/5.0
* Install PanDoc : https://pandoc.org/installing.html
* Unzip OneNote Md Exporter

## Usage

1. Open OneNote
   * Launch OneNote and be sure that notebooks to export are opened
2. Export
   * Start OneNoteMdExporter.exe
   * Choose the Notebook to export
   * Choose the destination format
   * Go take a coffee ☕
3. [For Joplin Users] Import
   * From Joplin windows app, File > Import > "RAW - Joplin Export Directory"

## Export format

### RAW Joplin folder

Comparison between OneNote Md Exporter and ENEX Export methods :

| | OneNote Md Exporter | ENEX Export |
| --- | --- | --- |
| Formatted content | ✅ | ✅ |
| Page Header | ✅ Note title removed from page content | 🟠 Note title in both Joplin note title and md file |
| Page Footer | ✅ No footer | 🟠 "Created by OneNote" |
| **Hierarchy of sections** | ✅ Sub-Notebooks | 🟠 Flattened as Tag |
| **Page order inside a section** | ✅ Sub-Notebooks | 🔴 All pages part of a single Notebook |
| **Page hierarchy (level)** | 🟠 Page title prefix <br/>(--- \<Page\>) | 🔴 |
| Note metadata | ✅ | ✅ |
| Image  | ✅ | ✅ |
| Table  | ✅ | ✅ |
| Table with nested image  | 🟠 Html table, image lost | ✅ Markdown |
| Attachments  | 🔴 | ✅ |
| Mark (\<mark\>)  | 🔴 | 🔴 |
| Drawing | 🟠 Flattened as image | 🟠 Flattened as image |
| Handwriting  | 🔴 Lost | 🟠 Flattened as image |
| Formula  | ? | ? |
| Revision history | 🔴 Lost | 🔴 Lost |
| Password protected sections | 🔴 Lost | 🔴 Lost |

### Markdown folder

Md file are created in folder hierarchy similar to OneNote Section hierarchy : *Notebook* \> *Section Group* \> *Section* -\> *Pages*.

Images are extracted in a *Ressource* folder at the root of the Notebook folder.

Joplin : this format can be used with Joplin *MD Markdown Directory* import, but it is not recommended because it will loose order of pages inside sections.

# Disclaimer

## Choose the right export method for your notes

If you are not using section and page hierarchy to organize your notes, EverNote migration can offer better results for you.

## Joplin format
⚠️ Future Joplin version may introduce modifications in the Joplin RAW Export Directory format preventing this tool to import correctly notebooks exported with this tool. I will do my best to keep the tool up-to-date. 

#  Contribution

In case of error or undesired behavior, please open an issue. 

Contribution are welcome, please open a PR.
