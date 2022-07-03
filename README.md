# Project Title

Personal Financal Category Parser

## Description

Program to parse a list of banking transaction categories stored as CVS format, and input them into an SQLite database.
The categories are hierarchical with categories and subcategories. The hiearchy in the CVS file is defined by 
indentations at the beginning of each line.

After the file is parsed, the categories are input into an SQLite database. If the category is a subcategory, the id field
of the parent category is stored in the parent_id field.

When the data is retrieved from the database it is stored in a searchable tree structure.

SQLAlchemy is used to interface with the database. 


## Getting Started

### Dependencies

* Python 3
* SQLAlchemy >= 1.2

### Executing program

```
python cats.py <csv_file>
```

## Authors

David Skarsten

## Version History

* 0.1
    * Initial Release

## License

This project is licensed under the MIT License - see the LICENSE.md file for details

## Acknowledgments

Inspiration, code snippets, etc.
* SQLAlchemy Adjancey List (https://docs.sqlalchemy.org/en/14/_modules/examples/adjacency_list/adjacency_list.html)
* QT TreeModel (https://code.qt.io/cgit/qt/qtbase.git/tree/examples/widgets/itemviews/simpletreemodel/treemodel.cpp?h=5.15)
* .Net TreeView (https://docs.microsoft.com/en-us/dotnet/api/system.windows.forms.treeview?view=windowsdesktop-6.0)
