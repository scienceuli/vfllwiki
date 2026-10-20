**Collabora Online** is a powerful online document editing suite. Integrate into your own infrastructure or access via one of our trusted hosting partners.

**Collabora Online** is a powerful online document editing suite. Integrate into your own infrastructure or access via one of our trusted hosting partners.

**Collabora Online Development Edition** (CODE) is the development version of Collabora Online. It is perfect for testing, home use or small teams, but not recommended for production environments.

### Integration with Nextcloud/ownCloud

Built around the Collabora Office core, builds are released on average once a month.

1. In Nextcloud/ownCloud, install the “Collabora Online” app
2. Go to Settings > Collabora Online
3. Set the server URL to `https://YOUR-COLLABORA-SERVER:9980`
4. Use the admin credentials to verify the connection

### Integration with Moodle

Install the plugin _mod_collabora_ (“Collabora Online” activity): Site administration → Plugins → Install plugins, upload the zip. Check supported versions on moodle.org first.

Under Site administration → Plugins → Activity modules → Collabora, set the Collabora URL to https://staging.doc.vfll.de (just the base address).

Add a “Collabora” activity to a course and open a document as a test.
If it fails with “unauthorized WOPI host”, check that https://YOUR-COLLABORA-SERVER:443 is in collabora_code_aliasgroups.

The plugin is stored in the moodle volume. The image copies fresh Moodle code into that volume when the version changes, so after a future moodle_image upgrade, check that the plugin is still there.
