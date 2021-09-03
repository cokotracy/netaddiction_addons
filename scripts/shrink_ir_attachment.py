# This script should be executed inside a NetAddiction Odoo 9 shell. It will
# remove all ir.attachment for res.partner's. This script can be be
# interrupted and restarted as many time as needed until all records have been
# removed.

self._cr.execute("SELECT id FROM ir_attachment WHERE res_model='res.partner'");
rows = self._cr.fetchall()
for count, row in enumerate(rows):
     print "Deleting ir_attachment ID " + str(row[0])
     self._cr.execute("delete from ir_attachment where id=" + str(format(row[0])))
     self._cr.commit()
     print "Done. " + str(len(rows) - count - 1) + " rows left to go"
