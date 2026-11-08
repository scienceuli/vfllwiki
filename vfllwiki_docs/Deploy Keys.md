# Deploy Keys

### Pros of deploy keys

- Anyone with access to the repository and server has the ability to deploy the project.
- Users don't have to change their local SSH settings.
- Deploy keys are read-only by default, but you can give them write access when adding them to a repository.

### Cons of deploy keys

- Deploy keys only grant access to a single repository. More complex projects may have many repositories to pull to the same server.
- Deploy keys are usually not protected by a passphrase, making the key easily accessible if the server is compromised.
- Deploy keys are credentials that don't have an expiry date.
- Deploy keys aren't linked directly to organization membership. If the user who created the deploy key is removed from the repository, the deploy key will still be active as it isn't tied to the specific user, but rather to the repository.

Wie lege ich einen Deploy Key an und bringe ihn auf github? Siehe [[Prozess - Deploy Key]]