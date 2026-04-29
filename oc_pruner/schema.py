# ISC License
#
# Copyright (c) 2026 Elia Rizzetto
#
# Permission to use, copy, modify, and/or distribute this software for any
# purpose with or without fee is hereby granted, provided that the above
# copyright notice and this permission notice appear in all copies.
#
# THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES WITH
# REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF MERCHANTABILITY AND
# FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR ANY SPECIAL, DIRECT,
# INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES WHATSOEVER RESULTING FROM
# LOSS OF USE, DATA OR PROFITS, WHETHER IN AN ACTION OF CONTRACT, NEGLIGENCE OR
# OTHER TORTIOUS ACTION, ARISING OUT OF OR IN CONNECTION WITH THE USE OR
# PERFORMANCE OF THIS SOFTWARE.

"""
Schema constants for validation reports.
"""


ERROR_TYPES = [
    "error",
    "warning"
]

ERROR_LABELS = [
    "br_id_existence",
    "br_id_format",
    "br_id_syntax",
    "date_format",
    "duplicate_br",
    "duplicate_citation",
    "duplicate_id",
    "duplicate_ra",
    "extra_space",
    "missing_citations",
    "missing_metadata",
    "orphan_ra_id",
    "orphan_venue_id",
    "page_format",
    "page_interval",
    "people_item_format",
    "publisher_format",
    "ra_id_existence",
    "ra_id_syntax",
    "required_fields",
    "required_value_cits",
    "row_semantics",
    "self-citation",
    "type_format",
    "uppercase_title",
    "venue_format",
    "volume_issue_format"
]

META_CSV_FIELDS = [
    "id",
    "title",
    "author",
    "pub_date",
    "venue",
    "volume",
    "issue",
    "page",
    "type",
    "publisher",
    "editor"
]

CITS_CSV_FIELDS = [
    "citing_id",
    "citing_publication_date",
    "cited_id",
    "cited_publication_date"
]