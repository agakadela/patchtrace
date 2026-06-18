# Fixture Notes

- The fixture represents a common auth patch where the route checks for a
  session but the data write still updates by project ID alone.
- Local materials do not include a two-user/manual test, database policies,
  row-level security rules, or production session configuration.
- The expected brief should separate authentication evidence from ownership
  enforcement evidence.
