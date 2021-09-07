# This script should be executed inside a NetAddiction Odoo 14 shell. It will
# run the ir.attachment post-upgrade resize cron until all images are resized.
# This script is idempotent and can be stopped and re-run at will.
# Please check the ir.cron ID before launching this script

CRON_ID = 3232

while self.env['ir.attachment'].search([("index_content", "=", "image_is_not_yet_resized"), ("res_field", "!=", False)]):
    print("Unresized attachments found. Starting cron.")
    self.env['ir.cron'].browse(CRON_ID).method_direct_trigger()
    print("Resize Batch completed. Committing to database")
    self._cr.commit()
