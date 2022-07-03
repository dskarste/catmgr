from sqlalchemy import Column
from sqlalchemy import Sequence
from sqlalchemy import ForeignKey
from sqlalchemy import Integer
from sqlalchemy import String
from sqlalchemy import Boolean
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import backref
#from sqlalchemy.orm import joinedload_all
from sqlalchemy.orm import relationship
from sqlalchemy.orm.collections import attribute_mapped_collection
from sqlalchemy.orm import Session
from sqlalchemy import literal
from sqlalchemy.orm import aliased
from sqlalchemy.sql import expression, functions
from sqlalchemy import types
from sqlalchemy.orm import validates
import sqlalchemy.exc

import csv
import re


Base = declarative_base()


class CategoryGroup(Base):
    __tablename__ = "category_group"
    id = Column(Integer, Sequence('category_group_id_seq'), primary_key=True)
    name = Column(String(50), nullable=False)
    # TODO: Define sequence function or class for maintaining order
    seq = Column(Integer)

    categories = relationship("Category", back_populates="group")

    def __repr__(self):
        return "<CategoryGroup(name=%r)>" % (self.name)


class Category(Base):
    __tablename__ = "category"
    id = Column(Integer, Sequence('category_id_seq'), primary_key=True)
    parent_id = Column(Integer, ForeignKey(id))
    name = Column(String(50), nullable=False)
    # Type: Type A, Type B, Type C
    # TODO: lookup table for types or validation?
    type = Column(String(50), nullable=False)
    description = Column(String(50))
    # group: Group A, Group B, Group C, Group D, Group E, Group F, Group G
    group_id = Column(Integer, ForeignKey('category_group.id'), nullable=False)
    # TODO: if tag is set, has_tag must be True
    has_tag = Column(Boolean(), default=False)
    # TODO: create table for tags
    tag = Column(String(50))
    hidden = Column(Boolean(), default=False)

    detail = (Column(Integer))
    group = relationship("CategoryGroup", back_populates="categories")

    children = relationship(
        "Category",
        cascade="all, delete-orphan",
        backref=backref("parent", remote_side=id),
    )

    #@validates('type')
    #def validate_type(self, key, type):
    #    assert type in ['Type A', 'Type B', 'Type C']

    def __init__(self, name=None, type=None, description=None, group_id=None, has_tag=False, tag=None, hidden=0, parent=None):
        self.name = name
        self.type = type
        self.description = description
        #self.category_group = category_group
        self.group_id = group_id
        # TODO: if tag is set, has_tag must be True
        self.has_tag = has_tag
        self.tag = tag
        self.hidden = hidden
        self.parent = parent

    def __repr__(self):
        return "<Category(name=%r, id=%r, parent_id=%r, type=%r, description=%r, group_id=%r, has_tag=%s, tag=%r, hidden=%r, detail=%r)>" % (
            self.name,
            self.id,
            self.parent_id,
            self.type,
            self.description,
            self.group_id,
            self.has_tag,
            self.tag,
            self.hidden,
            self.detail,
        )

    # dump method from SQLAlchemy Adjacency List example:
    # https://docs.microsoft.com/en-us/dotnet/api/system.windows.forms.treeview?view=windowsdesktop-6.0
    def dump(self, _indent=0):
        return (
            "   " * _indent
            + repr(self)
            + "\n"
            + "".join([c.dump(_indent + 1) for c in self.children])
        )


class TransactionCat:
    def __init__(self, id=None, parent_id=None, name=None, path=None, type=None, description=None, group=None, has_tag=None, tag=None, hidden=False):
        self.id = id
        self.parent_id = parent_id
        self.name = name
        self.path = path
        self.type = type
        self.description = description
        self.group = group
        self.has_tag = has_tag
        self.tag = tag


# Adapted from 
# https://code.qt.io/cgit/qt/qtbase.git/tree/examples/widgets/itemviews/simpletreemodel/treemodel.cpp?h=5.15
# and .net TreeModel
class Node:
    def __init__(self, data=None, parent=None, name=None, level=0, key=None):
        self.parent = parent
        self.children = list()
        self.data = data
        self.name = name
        self.level = level
        self.key = key

    @property
    def fullpath(self):
        path = '/' + self.name
        parent = self.parent
        while parent.parent is not None:
            path = '/' + parent.name + path
            parent = parent.parent
        self._fullpath = path
        return self._fullpath

    def iterate(self):
        pass

    def sort_children(self, key):
        pass

    # TODO: set parameters to handle existing nodes or create new one, aka multiple dispatch
    #def add_node(self, data, name=None):
    def add_node(self, node):
        #node = Node(data)
        print(f"Adding node: {node.name}")
        node.parent = self
        #node.name = name
        node.level = self.level+1
        self.children.append(node)

# TODO: root 
class TreeModel:
    def __init__(self, indent=0):
        self._root = Node()
        self.index = self._root
        self.indent = indent

    @property
    def root(self):
        return self._root

    def add_node(self, node=None):
        self._root.children.append(node)

    def fits_pattern(self, pattern, string):
        return re.search(pattern, string)

    def equal_pattern(self, pattern, string):
        return pattern == string

    # TODO: define lambda search for key, for generic search, maybe with re's, instead of strict name
    # TODO: define root, branch modes
    # TODO: return values: return as trees, lists, nodes, define with arg param, or whatever is most convenient?
    def search(self, name=None, key=None, path=None, comp=None, _node=None):
        if name is None:
            return self._root
        if _node is None:
            _node = self._root
        if path is None:
            path = 'node'
        if path not in ['node', 'root', 'branch']:
            raise ValueError("path must be 'node', 'full' or 'branch'")
        if comp is None:
            comp = lambda x, y: x == y

        # TODO: split function up into three different search functions for node, root and branch
        # TODO: maybe return back to this function and define as tree
        comp = lambda x, y: re.search(x, y)
        if _node.name is not None and comp(name, _node.name):
            if path == 'node':
                return [_node]
            # TODO: add deepcopy for new node
            elif path == 'root':
                return Node(data=_node.data, parent=None, name=_node.name, level=_node.level, key=_node.key)
            elif path == 'branch':
                n = Node(data=_node.data, parent=None, name=_node.name, level=_node.level, key=_node.key)
                # TODO: shallow copy of children, or deep copy?
                n.children = _node.children
                return n

        if path == 'node':
            nodes = list()
            for child in _node.children:
                retval = self.search(name=name, key=key, path=path, _node=child)
                nodes += retval
            return nodes
        elif path == 'root':
            n = Node(data=_node.data, parent=None, name=_node.name, level=_node.level, key=_node.key)
            for child in _node.children:
                retval = self.search(name=name, key=key, path=path, _node=child)
                if retval is not None:
                    n.add_node(retval)
            return n if n.children else None
        elif path == 'branch':
            n = Node(data=_node.data, parent=None, name=_node.name, level=_node.level, key=_node.key)
            for child in _node.children:
                retval = self.search(name=name, key=key, path=path, _node=child)
                if retval is not None:
                    n.add_node(retval)
            return n if n.children else None


def build_tcg_table(session):
    i=1
    for name in ([
        'Group A',
        'Group B',
        'Group C',
        'Group D',
        'Group E',
        'Group F',
        'Group G',
    ]):
        session.add(CategoryGroup(name=name, seq=i))
        i+=1
    session.commit()


def create_new_category(cat, groups):
    cat.pop(None, None)

    cat = {k: (v.strip() if v is not None else None) for k, v in cat.items()}
    cat = {k: (v if v != '' else None) for k, v in cat.items()}

    if cat['category_group'] is not None:
        grp = cat['category_group']
        try:
            cat['group_id'] = groups[grp]
        except KeyError:
            print(f"Group not found: {grp}")
    del cat['category_group']

    if cat['tag'] is not None:
        cat['has_tag'] = True
        cat['tag'] = cat['tag'].split('T')[0].strip()
        cat['tag'] = cat['tag'] if cat['tag'] != '' else None
    else:
        cat['has_tag'] = False

    cat['hidden']=True if cat['hidden'] == 'H' else False

    return Category(**cat)


def read_csv(file=None, fieldnames=None):
    with open(file, newline='') as csvfile:
        rowreader = list(csv.DictReader(csvfile, delimiter=',', quotechar='"', fieldnames=fieldnames))
        return list(rowreader)


def the_maury_povich_show(data, groups):
    # AKA, who's your daddy?
    ilen = 3
    level = indent = 0
    parent = None
    root = children = list()
    #root = Category(name='root', parent=None, group_id=0, type='')
    #children = root.children

    for r in data:
        name = r['name']
        indent = len(name) - len(name.lstrip())
        newlevel = int(indent / ilen)

        node = create_new_category(r, groups)

        if newlevel == level:
            children.append(node)
        elif newlevel == level+1:
            parent = sibling
            children = parent.children
            children.append(node)
        elif newlevel < level:
            for i in range(newlevel, level):
                parent = getattr(parent, 'parent', None)
            children = getattr(parent, 'children', root)
            children.append(node)
        sibling = node
        level = newlevel

    return root


def import_csv(session):
    has_header=True
    fieldnames = ['name','type','description','category_group','tag','hidden']
    file = r'Categories.csv'

    groups = dict()
    for g in session.query(CategoryGroup):
        groups[g.name] = g.id

    data = read_csv(file, fieldnames)
    if has_header:
        data = data[1:]
    categories = the_maury_povich_show(data, groups)
    session.add_all(categories)
    session.commit()


def load_data(session, name=None, path=None, group=None, show_hidden=False, has_tag=None, tag=None):
    if name is not None:
        name = re.sub('_', '/_', name)
    if path is not None:
        path = re.sub('_', '/_', path)
    if tag is not None:
        tag = re.sub('_', '/_', tag)
    tc_tree = \
        session.query(
            Category.id.label('id'),
            Category.name.label('name'),
            ('/' + Category.name).label('path'),
            #literal('').label('path'),
            literal(0).label('level'),
            Category.parent_id.label('parent_id'),
            CategoryGroup.name.label('group'),
            #literal(None).label('group'),
            Category.description.label('description'),
            Category.has_tag.label('has_tag'),
            Category.tag.label('tag'),
            Category.hidden.label('hidden'),
        ) \
        .filter(Category.parent_id == None) \
        .filter(CategoryGroup.id == Category.group_id) \
        .cte(name='cat_tree', recursive=True)

    tree_alias = aliased(tc_tree, name='tr')
    cat_alias = aliased(Category, name='tc')

    tc_tree = tc_tree.union_all(
        session.query(
            cat_alias.id,
            cat_alias.name,
            (tree_alias.c.path + '/' + cat_alias.name),
            tree_alias.c.level + 1,
            tree_alias.c.id,
            tree_alias.c.group,
            cat_alias.description,
            cat_alias.has_tag,
            cat_alias.tag,
            cat_alias.hidden
        ) \
        .filter(cat_alias.parent_id == tree_alias.c.id)
    )
    #tc_tree = session.query(tc_tree).filter(tc_tree.c.level > 0)
    tc_tree = session.query(tc_tree)

    return [
        TransactionCat(
            id = row.id,
            parent_id = row.parent_id,
            name = row.name,
            path = row.path,
            group = row.group,
            description = row.description,
            has_tag = row.has_tag,
            tag = row.tag)
        for row in tc_tree ]

    #return tc_tree

    categories = tc_tree.union_all(
        session.query(
            Category.id,
            Category.name,
            ('/' + Category.name),
            literal(0).label('level'),
            literal(None),
            CategoryGroup.name,
            Category.description,
            Category.has_tag,
            Category.tag,
            Category.hidden
        ) \
        .filter(Category.parent_id == None) \
        .filter(CategoryGroup.id == Category.group_id)
    )
    return categories

    if name is not None:
        #categories = categories.filter(Category.name.like(name+'%', escape='/'))
        categories = categories.filter(Category.name == name)
    #if path is not None:
    #    categories = categories.filter(tc_alias.c.path.like(path+'%', escape='/'))
    if group is not None:
        categories = categories.filter(CategoryGroup.name == group)
    if show_hidden is False:
        categories = categories.filter(Category.hidden != True)
    if has_tag is not None:
        categories = categories.filter(Category.has_tag == has_tag)
    if tag is not None:
        categories = categories.filter(Category.tag.like(tag+'%', escape='/'))
    results = categories.order_by(path)
    print()
    print()
    print(results)
    print()



# TODO: New category inherits everythin from parents
# TODO: Or, if top level, needs everything defined.
# TODO: Create here, or return to calling program to finish adding to DB?
# TODO: set default type based on group
# TODO: Add quality controls
def add_new_category(session, name=None, parent_name=None, type=None, group_name=None,
                        description=None, has_tag=None, tag=None, hidden=None):

    parent = None

    # TODO: error if parent category doesn't exist
    if parent_name is not None:
        parent = session.query(Category) \
                .filter(Category.name == parent_name).one()
    group = session.query(CategoryGroup) \
            .filter(CategoryGroup.name == group_name).one()

    tc = Category(name, parent=parent, type=type, group_id=group.id, description=description,
            has_tag=has_tag, tag=tag, hidden=hidden)
    session.add(tc)


def modify_category(session, **kwargs):
    tc = session.query(Category).filter(Category.id == kwargs['id']).one()

    if 'name' in kwargs:
        tc.name = kwargs['name']
    if 'parent_id' in kwargs:
        tc.parent_id = kwargs['parent_id']
    if 'type' in kwargs:
        tc.type = kwargs['type']
    if 'description' in kwargs:
        tc.description = kwargs['description']
    if 'has_tag' in kwargs:
        tc.has_tag = kwargs['has_tag']
    if 'tag' in kwargs:
        tc.tag = kwargs['tag']
    if 'hidden' in kwargs:
        tc.hidden = kwargs['hidden']

    print(tc.description)


def delete_category(session, **kwargs):
    print(kwargs)
    tc = session.query(Category).filter_by(**kwargs).delete()


# TODO: Finish display
def view_category_table(categories):
    i=1
    for row in categories:
        id = row.id or ''
        parent_id = row.parent_id or ''
        path = row.path or ''
        name = row.name or ''
        group = row.group or ''
        description = row.description or ''
        has_tag = row.has_tag or ''
        tag = row.tag or ''
        indent = path.count('/')
        name = (' ' * indent*4) + name
        #print("{:>"+str(i)+"}").format('hello')
        print(f"{i:>3} {id:4} {parent_id:3} {name:45}{path:45}{group:27}{has_tag:<5}{tag:5}")
        i+=1


def view_category_search(tree=None, pattern=None):
    indent = 5

    if pattern is None:
        text = view_descendent_hierarchy(node=tree.root, indent=indent)
    else:
        nodes = tree.search(name=pattern, path='node', comp=(lambda x,y: re.search(x,y)))
        text = ''
        for node in nodes:
            level=0
            level, txt = view_ancestor_hierarchy(node=node, indent=indent, level=level)
            text += txt
            text += view_descendent_hierarchy(node=node, pattern=pattern, indent=indent, level=level+1)
    text = text.strip()
    if pattern is not None:
        text = text.replace(pattern, '\033[0;33m{}\033[m'.format(pattern))
    categories = text.split('\n')
    [print(f" {i+1:<5}   {categories[i]}") for i in range(0, len(categories))]


def view_ancestor_hierarchy(node=None, indent=0, pattern=None, level=0):
    path = node.fullpath.split('/')[1:]
    text = ''
    for item in path:
        text += ' ' * indent*level + item + '\n'
        level+=1
    return (level, text)


def view_descendent_hierarchy(node=None, indent=3, pattern=None, level=0):
    return (
        ''.join([
            ' ' * indent*level + c.name
            + '\n'
            + view_descendent_hierarchy(node=c, indent=indent, pattern=pattern, level=level+1)
            for c in node.children
        ])
    )


def create_tc(categories):
    cats = [
        (TransactionCat(
            id = c.id,
            parent_id = c.parent_id,
            name = c.name,
            path = c.path,
            group = c.group,
            description = c.description,
            has_tag = c.has_tag,
            tag = c.tag
        ))
        for c in categories
    ]

    return cats

# 1. Load hash records with items keyed by parent_id
# 2. Set node to root of tree
# 3. while the list of children nodes is not exhausted:
#    a. get list of items from hash keyed by parent_id
#    b. for each item:
#       1. create a new child node for item
#       2. add child node to children nodes of current node
def setup_tree_model(data):
    parents = dict()
    for item in data:
        if item.parent_id not in parents:
            parents[item.parent_id] = list()
        parents[item.parent_id].append(item)

    stack = list()
    tree = TreeModel()
    node = tree.root
    level = 0
    i = 0

    while node is not None:
        key = node.key
        children = parents[key]
        while True:
            if i < len(children):
                child = children[i]
                n = Node(data=child, parent=node, name=child.name, level=level+1, key=child.id)
                node.children.append(n)
                i += 1
                if child.id in parents:
                    stack.append((node, i))
                    node = n
                    i = 0
                    level = node.level
                    break
            else:  # if no children left:
            #   TODO: pop state off stack
                if stack:
                    (node, i) = stack.pop()
                    level = node.level
                else:
                    node = None
            #   break to main loop
                break
    return tree


# Functions:
# Search by pattern or all
# Add
# Modify - by search or direct
#   name
#   type (type a, type b, type c)
#   description
#   group
#   has_tag
#   tag
#   hidden
#   parent
# Delete


# add
# modify
# delete
# list all
# search
def main():
    #engine = create_engine("sqlite:///categories.db", echo=True)
    tables = [Base.metadata.tables['category'],
              Base.metadata.tables['category_group']]
    engine = create_engine("sqlite://", echo=False)
    Base.metadata.create_all(engine, tables=tables)
    session = Session(engine)

    build_tcg_table(session)
    import_csv(session)

    # TODO: Child should inherit type and group from parent
    add_new_category(session, name='new cat', parent_name=None, type='Type B', group_name='Group C')
    add_new_category(session, name='new cat 2', parent_name='Cat 2', type='Type A', group_name='Group B')
    #add_new_category(session, name='new cat 3', parent_name="Cat doesn't exist", type='Type A', group_name='Group D')

    delete_category(session, id=3)
    modify_category(session, id=2, name='Modified category', type='Type B')
    session.commit()

    # TODO: move following two lines to separate function
    data = load_data(session, show_hidden=False, group='Group A')
    #categories = create_tc(data)
    categories = data

    view_category_table(sorted(categories, key=lambda x: x.path))
    tree = setup_tree_model(categories)

    view_category_search(tree=tree, pattern='Cat 1')

    print()
    node = tree.search(name='Cat 1', path='branch')
    print(node)
    print(node.children[0].fullpath)
    print(node.children[0].children[0].fullpath)
    print(node.children[0].children[0].children[0].fullpath)
    print(node.children[0].children[0].children[1].fullpath)


if __name__ == "__main__":
    main()
