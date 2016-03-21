import re, json

class Config(object):

    re_comment = re.compile(r"""^#.*$""")
    re_section_start = re.compile(r"""^<(?P<name>[^/\s>]+)\s*(?P<value>[^>]+)?>$""")
    re_section_end = re.compile(r"""^</(?P<name>[^\s>]+)\s*>$""")

    def __init__(self, name, values=[]):
        self.name = name
        self.values = values
        self.attributes = []
        self.children = []

        
    def set_attribute(self, name, values ):
        setattr( self, name, values )
        self.attributes.append( name )
        
        
    def add_child(self, name, values):
        child = Config(name, values)
        self.children.append(child)
        child.parent = self
        self.attributes.append( child )

        attr = getattr( self, name, None )
        if attr != None:
            if type(attr) == list:
                attr.append( child )
            else:
                attr = [attr,child,]
            setattr( self, name, attr )
        else:
            setattr( self, name, child )

        return child


    def find(self, path):
        """Return the first element wich matches the path.
        """
        pathelements = path.strip("/").split("/")
        if pathelements[0] == '':
            return self
        return self._find(pathelements)


    def _find(self, pathelements):
        if pathelements: # there is still more to do ...
            next = pathelements.pop(0)
            for child in self.children:
                if child.name == next:
                    result = child._find(pathelements)
                    if result:
                        return result
            return None
        else: # no pathelements left, result is self
            return self


    def findall(self, path):
        """Return all elements wich match the path.
        """
        pathelements = path.strip("/").split("/")
        if pathelements[0] == '':
            return [self]
        return self._findall(pathelements)


    def _findall(self, pathelements):
        if pathelements: # there is still more to do ...
            result = []
            next = pathelements.pop(0)
            for child in self.children:
                if child.name == next:
                    result.extend(child._findall(pathelements))
            return result
        else: # no pathelements left, result is self
            return [self]
            

    def print_xml(self, indent = -1):
        """Recursively print nodes in xml format.
        """
        if len(self.children) > 0:
            if indent >= 0:
                print ("    " * indent + "<" + self.name + " " + " ".join(self.values) + ">")
            for child in self.children:
                child.print_r(indent + 1)
            if indent >= 0:
                print ("    " * indent + "</" + self.name + ">")
        else:
            if indent >= 0:
                print( "    " * indent + self.name + " " + " ".join(self.values))

                
    def print_json(self, indent = 0):
        """Recursively print nodes in json format.
        """
        if indent == 0:
            print("{")
            indent += 1

        if self.values != []:
            print ("    " * indent + '"attributes": %s,'%json.dumps(self.values))
        for attribute in self.attributes[:-1]:
            if type(attribute) != Config:
                print( "    " * indent + '"' + attribute + '":' + json.dumps(getattr(self, attribute, None)) + ",")
            else:
                print ("    " * indent + '"' + attribute.name + '":{')
                attribute.print_json(indent+1)
                print ("    " * indent + "},")
        else:
            if type(self.attributes[-1]) != Config:
                print( "    " * indent + '"' + self.attributes[-1] + '":' + json.dumps(getattr(self, self.attributes[-1], None)) )
            else:
                print ("    " * indent + '"' + self.attributes[-1].name + '":{')
                self.attributes[-1].print_json(indent+1)
                print ("    " * indent + "}")
        
        if indent == 1:
            print("}")
                

    @classmethod
    def parse_file(cls, file):
        """Parse a file.
        """
        f = open(file)
        root = cls._parse(f)
        f.close()
        return root


    @classmethod
    def parse_string(cls, string):
        """Parse a string.
        """
        return cls._parse(string.splitlines())


    @classmethod
    def _parse(cls, itobj):
        root = node = Config('root')
        for line in itobj:
            line = line.strip()

            # Check for empty line or comment and skip if found
            if (len(line) == 0) or cls.re_comment.match(line):
                continue

            # Check if line contains the start of a section and add a child if found
            match = cls.re_section_start.match(line)
            if match:
                values = match.group("value").split()
                node = node.add_child(match.group("name"), values)
                continue

            # Check if line contains the end of a section and revert back to parent if found
            match = cls.re_section_end.match(line)
            if match:
                if node.name != match.group("name"):
                    raise Exception("Section mismatch: '"+match.group("name")+"' should be '"+node.name+"'")
                node = node.parent
                continue
            
            # Line is not start or end of section so must be name, value pair. Add attribute to nodes attribute list and set class attribute.
            values = line.split()
            name = values.pop(0)
            if len(values) == 1:
                values = values[0].strip('"')
            node.set_attribute(name, values)
        return root

       
    
sample="""
#ServerType standalone
ServerRoot "/usr/local/apache"
LockFile /var/lock/apache.lock
<Directory />
        Options FollowSymLinks
        AllowOverride None
        Order deny,allow
        Deny from all
</Directory>
<Directory "/share/Qweb">
        Options FollowSymLinks MultiViews
        AllowOverride All
        Order allow,deny
        Allow from all
</Directory>

AccessFileName .htaccess
<FilesMatch "^\.ht">
    Order allow,deny
    Deny from all
    Satisfy All
</FilesMatch>

<IfModule log_config_module>
    LogFormat "%h %l %u %t \"%r\" %>s %b \"%{Referer}i\" \"%{User-Agent}i\"" com                                                                            bined
    LogFormat "%h %l %u %t \"%r\" %>s %b" common
    LogFormat "%{Referer}i -> %U" referer
    LogFormat "%{User-agent}i" agent

    <IfModule logio_module>
      LogFormat "%h %l %u %t \"%r\" %>s %b \"%{Referer}i\" \"%{User-Agent}i\" 
    </IfModule>
    #CustomLog logs/access_log common
    #
    # If you prefer a logfile with access, agent, and referer information
    # (Combined Logfile Format) you can use the following directive.
    #
    #CustomLog logs/access_log combined
</IfModule>

<IfModule autoindex_module>
                AddIconByEncoding (CMP,/icons/compressed.gif) x-compress x-gzip

                AddIcon /icons/blank.gif ^^BLANKICON^^
                DefaultIcon /icons/unknown.gif

</IfModule>
Include /etc/config/apache/extra/apache-fastcgi.conf
"""
a=Config.parse_string(sample)
a.print_json()