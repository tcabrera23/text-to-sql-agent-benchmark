"""DDL de la base de datos Chinook: fuente única usada por los prompts de los agentes
y por el arena (antes duplicado de forma completa en main.py/llm_arena.py y de forma
condensada en arena_runner.py)."""

CHINOOK_SCHEMA_DDL = """
CREATE TABLE "artists" (
    "ArtistId" INTEGER NOT NULL,
    "Name" NVARCHAR(120),
    PRIMARY KEY ("ArtistId")
);
CREATE TABLE "albums" (
    "AlbumId" INTEGER NOT NULL,
    "Title" NVARCHAR(160) NOT NULL,
    "ArtistId" INTEGER NOT NULL,
    PRIMARY KEY ("AlbumId"),
    FOREIGN KEY ("ArtistId") REFERENCES "artists" ("ArtistId")
);
CREATE TABLE "employees" (
    "EmployeeId" INTEGER NOT NULL,
    "LastName" NVARCHAR(20) NOT NULL,
    "FirstName" NVARCHAR(20) NOT NULL,
    "Title" NVARCHAR(30),
    "ReportsTo" INTEGER,
    "BirthDate" DATETIME,
    "HireDate" DATETIME,
    "Address" NVARCHAR(70),
    "City" NVARCHAR(40),
    "State" NVARCHAR(40),
    "Country" NVARCHAR(40),
    "PostalCode" NVARCHAR(10),
    "Phone" NVARCHAR(24),
    "Fax" NVARCHAR(24),
    "Email" NVARCHAR(60),
    PRIMARY KEY ("EmployeeId"),
    FOREIGN KEY ("ReportsTo") REFERENCES "employees" ("EmployeeId")
);
CREATE TABLE "customers" (
    "CustomerId" INTEGER NOT NULL,
    "FirstName" NVARCHAR(40) NOT NULL,
    "LastName" NVARCHAR(20) NOT NULL,
    "Company" NVARCHAR(80),
    "Address" NVARCHAR(70),
    "City" NVARCHAR(40),
    "State" NVARCHAR(40),
    "Country" NVARCHAR(40),
    "PostalCode" NVARCHAR(10),
    "Phone" NVARCHAR(24),
    "Fax" NVARCHAR(24),
    "Email" NVARCHAR(60) NOT NULL,
    "SupportRepId" INTEGER,
    PRIMARY KEY ("CustomerId"),
    FOREIGN KEY ("SupportRepId") REFERENCES "employees" ("EmployeeId")
);
CREATE TABLE "invoices" (
    "InvoiceId" INTEGER NOT NULL,
    "CustomerId" INTEGER NOT NULL,
    "InvoiceDate" DATETIME NOT NULL,
    "BillingAddress" NVARCHAR(70),
    "BillingCity" NVARCHAR(40),
    "BillingState" NVARCHAR(40),
    "BillingCountry" NVARCHAR(40),
    "BillingPostalCode" NVARCHAR(10),
    "Total" NUMERIC(10, 2) NOT NULL,
    PRIMARY KEY ("InvoiceId"),
    FOREIGN KEY ("CustomerId") REFERENCES "customers" ("CustomerId")
);
CREATE TABLE "invoice_items" (
    "InvoiceLineId" INTEGER NOT NULL,
    "InvoiceId" INTEGER NOT NULL,
    "TrackId" INTEGER NOT NULL,
    "UnitPrice" NUMERIC(10, 2) NOT NULL,
    "Quantity" INTEGER NOT NULL,
    PRIMARY KEY ("InvoiceLineId"),
    FOREIGN KEY ("InvoiceId") REFERENCES "invoices" ("InvoiceId"),
    FOREIGN KEY ("TrackId") REFERENCES "tracks" ("TrackId")
);
CREATE TABLE "media_types" (
    "MediaTypeId" INTEGER NOT NULL,
    "Name" NVARCHAR(120),
    PRIMARY KEY ("MediaTypeId")
);
CREATE TABLE "genres" (
    "GenreId" INTEGER NOT NULL,
    "Name" NVARCHAR(120),
    PRIMARY KEY ("GenreId")
);
CREATE TABLE "tracks" (
    "TrackId" INTEGER NOT NULL,
    "Name" NVARCHAR(200) NOT NULL,
    "AlbumId" INTEGER,
    "MediaTypeId" INTEGER NOT NULL,
    "GenreId" INTEGER,
    "Composer" NVARCHAR(220),
    "Milliseconds" INTEGER NOT NULL,
    "Bytes" INTEGER,
    "UnitPrice" NUMERIC(10, 2) NOT NULL,
    PRIMARY KEY ("TrackId"),
    FOREIGN KEY ("AlbumId") REFERENCES "albums" ("AlbumId"),
    FOREIGN KEY ("GenreId") REFERENCES "genres" ("GenreId"),
    FOREIGN KEY ("MediaTypeId") REFERENCES "media_types" ("MediaTypeId")
);
CREATE TABLE "playlists" (
    "PlaylistId" INTEGER NOT NULL,
    "Name" NVARCHAR(120),
    PRIMARY KEY ("PlaylistId")
);
CREATE TABLE "playlist_track" (
    "PlaylistId" INTEGER NOT NULL,
    "TrackId" INTEGER NOT NULL,
    PRIMARY KEY ("PlaylistId", "TrackId"),
    FOREIGN KEY ("PlaylistId") REFERENCES "playlists" ("PlaylistId"),
    FOREIGN KEY ("TrackId") REFERENCES "tracks" ("TrackId")
);
"""
