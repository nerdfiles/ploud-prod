""" create template """


def create_site(conn, id, template_id=None, type=None):
    if type is None:
        type = 'plone41'

    if template_id:
        prefix = 'ploud%s'%template_id
        template = 'template_%s'%type
    else:
        prefix = 'template_%s'%type
        template = prefix

    # Create the database.
    cursor = conn.cursor()

    # FIXME: Create a stored procedure.
    cursor.execute(
        """
CREATE TABLE ploud%(id)s_blob_chunk
              (LIKE %(tp1)s_blob_chunk INCLUDING ALL);

CREATE TABLE ploud%(id)s_commit_lock
              (LIKE %(tp1)s_commit_lock INCLUDING ALL);

CREATE TABLE ploud%(id)s_object_state
              (LIKE %(tp1)s_object_state INCLUDING ALL);


CREATE OR REPLACE FUNCTION ploud%(id)s_blob_chunk_delete_trigger() RETURNS TRIGGER
AS $blob_chunk_delete_trigger$
    -- Version: 1.5B
    -- Unlink large object data file after blob_chunk row deletion
    DECLARE
        cnt integer;
    BEGIN
        SELECT count(*) into cnt FROM ploud%(id)s_blob_chunk WHERE chunk=OLD.chunk;
        IF (cnt = 1) THEN
            -- Last reference to this oid, unlink
            PERFORM lo_unlink(OLD.chunk);
        END IF;
        RETURN OLD;
    END;
$blob_chunk_delete_trigger$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION ploud%(id)s_temp_blob_chunk_delete_trigger() RETURNS TRIGGER
AS $temp_blob_chunk_delete_trigger$
    -- Version: 1.5B
    -- Unlink large object data file after temp_blob_chunk row deletion
    DECLARE
        cnt integer;
    BEGIN
        SELECT count(*) into cnt FROM ploud%(id)s_blob_chunk WHERE chunk=OLD.chunk;
        IF (cnt = 0) THEN
            -- No more references to this oid, unlink
            PERFORM lo_unlink(OLD.chunk);
        END IF;
        RETURN OLD;
    END;
$temp_blob_chunk_delete_trigger$ LANGUAGE plpgsql;

INSERT INTO ploud%(id)s_object_state
              SELECT * FROM %(tp)s_object_state;

INSERT INTO ploud%(id)s_blob_chunk
              SELECT * FROM %(tp)s_blob_chunk;

        """ % {'id': id, 'tp': prefix, 'tp1': template})

    cursor.execute("SELECT last_value FROM %s_zoid_seq"%prefix)
    cursor.execute("CREATE SEQUENCE ploud%s_zoid_seq START WITH %s"%(
            id, cursor.fetchone()[0]))
