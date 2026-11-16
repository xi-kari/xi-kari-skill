---
title: "GitLab 2017: service returned while some data remained lost"
description: "Separate availability, data completeness, and the readiness of recovery arrangements."
kind: "Documented case"
source_type: "Corporate incident postmortem"
---

# GitLab 2017: service returned while some data remained lost

On January 31, 2017, the data directory of GitLab.com’s primary database was accidentally deleted. GitLab’s February 10 postmortem describes service returning after roughly eighteen hours while roughly six hours of database changes remained unrecovered. The account is the organization’s own retrospective report, not an independent investigation.

## Which recovery path actually worked?

The report distinguishes four arrangements:

| Arrangement | Reported condition during the incident |
| --- | --- |
| Daily `pg_dump` backups | The backup tool was version 9.2 against a 9.6 database; jobs aborted, the bucket was empty, and error mail was rejected. |
| Azure disk snapshots | Used for other servers, but not enabled for the database servers. |
| Primary/secondary replication | The secondary had been cleared for rebuilding and the primary was accidentally cleared; neither supplied the required recovery. |
| LVM snapshots for staging | A routine snapshot was nearly 24 hours old; a manually created load-testing snapshot was about six hours old and was used. |

Copying data from staging back to production took about eighteen hours, with staging’s slow disks as a bottleneck. Webhooks had been removed from the staging database to avoid unintended calls, so they had to be exported separately from the snapshot and restored. The report records the database returning at 17:00 UTC on February 1 and webhooks being restored around 18:00. See [“Broken recovery procedures” and “Recovering GitLab.com”](https://about.gitlab.com/blog/postmortem-of-database-outage-of-january-31/).

The restored database reflected the snapshot at 17:20 UTC on January 31. Later changes to database-held projects, comments, users, issues, and snippets were lost. Git repositories and wikis were stored separately and were not lost, but were unavailable during the outage. Content survival and availability at the needed time are distinct.

## What had recovered?

[§6.6](/en/theory/part-06#section-6-6) asks what recovered, for whom, under what support, and as of when. Service availability and database completeness therefore receive different answers. The lost changes do not negate the restored service, and restored service does not restore the lost changes.

The report does not identify a pre-published recovery target in the framework’s terms. This page uses its records to clarify the scope of a recovery statement, without retroactively treating the incident as a formal repair test.

## Recovery arrangements still open {#recovery-reserve}

As of the February 10 report, the secondary database was being rebuilt and `pg_dump` backups were paused; the latest was three days old. LVM snapshots had moved to hourly operation. Azure snapshots were still being investigated, while automated restoration testing and other improvements appeared on an in-progress list. See [“Improving recovery procedures”](https://about.gitlab.com/blog/postmortem-of-database-outage-of-january-31/#improving-recovery-procedures).

These entries distinguish a completed schedule change from unfinished work. They do not show that recovery margins were fully restored or that the new arrangements succeeded in a later incident. An hourly snapshot interval concerns the age of potentially recoverable data; it is not an estimate of how long restoration takes.

## Source and limits

GitLab, [Postmortem of database outage of January 31](https://about.gitlab.com/blog/postmortem-of-database-outage-of-january-31/), February 10, 2017; sections cited above. The statuses are historical, not descriptions of GitLab today. This page does not allocate personal liability from the incident narrative.

Read [recovery](../concepts/recovery), [§6.10](/en/theory/part-06#section-6-10), and [D.31](/en/theory/appendix-d/d-31#section-d-31).
