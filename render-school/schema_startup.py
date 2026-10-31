"""Avoid repeating exclusive table DDL while a previous deployment serves traffic."""
from sqlalchemy import text

def secure_postgres_tables(conn,metadata):
    for table in metadata.sorted_tables:
        state=conn.execute(text("""SELECT c.relrowsecurity AS rls,
            EXISTS(SELECT 1 FROM aclexplode(COALESCE(c.relacl,acldefault('r',c.relowner))) a WHERE a.grantee=0) AS public_grants
            FROM pg_class c JOIN pg_namespace n ON n.oid=c.relnamespace
            WHERE c.relname=:name AND n.nspname=current_schema()"""),{'name':table.name}).mappings().one()
        # Existing secured tables need no AccessExclusiveLock during a rolling deploy.
        if not state['rls']:conn.execute(text(f'ALTER TABLE {table.name} ENABLE ROW LEVEL SECURITY'))
        if state['public_grants']:conn.execute(text(f'REVOKE ALL ON TABLE {table.name} FROM PUBLIC'))
