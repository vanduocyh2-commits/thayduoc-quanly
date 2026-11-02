from types import SimpleNamespace
from schema_startup import secure_postgres_tables

class Connection:
 def __init__(self,flags):self.flags=flags;self.calls=[]
 def execute(self,query,params=None):
  self.calls.append((str(query),params))
  if params:self.current=self.flags[params['name']]
  return self
 def mappings(self):return self
 def one(self):return self.current

def test_secured_existing_tables_do_not_repeat_exclusive_schema_changes():
 db=Connection({'school_existing':dict(rls=True,public_grants=False)})
 secure_postgres_tables(db,SimpleNamespace(sorted_tables=[SimpleNamespace(name='school_existing')]))
 assert len(db.calls)==1 and db.calls[0][0].startswith('SELECT')

def test_new_or_exposed_tables_keep_row_security_and_revoke_public_access():
 db=Connection({'school_new':dict(rls=False,public_grants=True),'school_private':dict(rls=False,public_grants=False)})
 secure_postgres_tables(db,SimpleNamespace(sorted_tables=[SimpleNamespace(name=n) for n in db.flags]))
 sql=[q for q,p in db.calls if p is None]
 assert sql==['ALTER TABLE school_new ENABLE ROW LEVEL SECURITY','REVOKE ALL ON TABLE school_new FROM PUBLIC','ALTER TABLE school_private ENABLE ROW LEVEL SECURITY']
