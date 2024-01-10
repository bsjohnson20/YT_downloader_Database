-- SQLite
DELETE FROM videos
WHERE rowid = (
    SELECT rowid
    FROM videos
    WHERE channel = '<channel>'
    LIMIT 1
);
