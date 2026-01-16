"""
Tests de consultas SQL para evaluar LLMs en el LLM Arena
Organizados por niveles de dificultad: Básico, Medio, Avanzado
"""

# ==============================================================================
# NIVEL BÁSICO (Dificultad 1/5)
# SELECT simple, filtros básicos, agregaciones simples
# ==============================================================================

BASIC_TESTS = [
    {
        "id": "B1",
        "description": "Lista los 10 artistas con más álbumes",
        "expected_tables": ["artists", "albums"],
        "expected_operations": ["JOIN", "GROUP BY", "COUNT", "ORDER BY", "LIMIT"],
        "correct_sql": """
            SELECT a.Name, COUNT(al.AlbumId) as TotalAlbums
            FROM artists a
            JOIN albums al ON a.ArtistId = al.ArtistId
            GROUP BY a.ArtistId, a.Name
            ORDER BY TotalAlbums DESC
            LIMIT 10
        """
    },
    {
        "id": "B2",
        "description": "¿Cuántos clientes hay en cada país?",
        "expected_tables": ["customers"],
        "expected_operations": ["GROUP BY", "COUNT", "ORDER BY"],
        "correct_sql": """
            SELECT Country, COUNT(CustomerId) as TotalCustomers
            FROM customers
            GROUP BY Country
            ORDER BY TotalCustomers DESC
        """
    },
    {
        "id": "B3",
        "description": "Muestra el total de ventas (suma de Total) por cada año",
        "expected_tables": ["invoices"],
        "expected_operations": ["GROUP BY", "SUM", "strftime"],
        "correct_sql": """
            SELECT strftime('%Y', InvoiceDate) as Year, 
                   SUM(Total) as TotalSales
            FROM invoices
            GROUP BY Year
            ORDER BY Year
        """
    },
    {
        "id": "B4",
        "description": "Lista los 5 géneros musicales más populares por cantidad de canciones",
        "expected_tables": ["genres", "tracks"],
        "expected_operations": ["JOIN", "GROUP BY", "COUNT", "ORDER BY", "LIMIT"],
        "correct_sql": """
            SELECT g.Name, COUNT(t.TrackId) as TotalTracks
            FROM genres g
            JOIN tracks t ON g.GenreId = t.GenreId
            GROUP BY g.GenreId, g.Name
            ORDER BY TotalTracks DESC
            LIMIT 5
        """
    },
    {
        "id": "B5",
        "description": "¿Cuál es el precio promedio de una canción por género?",
        "expected_tables": ["genres", "tracks"],
        "expected_operations": ["JOIN", "GROUP BY", "AVG"],
        "correct_sql": """
            SELECT g.Name, ROUND(AVG(t.UnitPrice), 2) as AvgPrice
            FROM genres g
            JOIN tracks t ON g.GenreId = t.GenreId
            GROUP BY g.GenreId, g.Name
            ORDER BY AvgPrice DESC
        """
    }
]

# ==============================================================================
# NIVEL MEDIO (Dificultad 3/5)
# JOINs múltiples, subconsultas simples, agregaciones complejas
# ==============================================================================

MEDIUM_TESTS = [
    {
        "id": "M1",
        "description": "¿Cuáles son los 5 clientes que más han gastado y cuánto gastaron?",
        "expected_tables": ["customers", "invoices"],
        "expected_operations": ["JOIN", "GROUP BY", "SUM", "ORDER BY", "LIMIT"],
        "correct_sql": """
            SELECT c.FirstName || ' ' || c.LastName as CustomerName,
                   c.Country,
                   SUM(i.Total) as TotalSpent
            FROM customers c
            JOIN invoices i ON c.CustomerId = i.CustomerId
            GROUP BY c.CustomerId
            ORDER BY TotalSpent DESC
            LIMIT 5
        """
    },
    {
        "id": "M2",
        "description": "Muestra las ventas por empleado (agente de soporte) y el número de clientes que atiende cada uno",
        "expected_tables": ["employees", "customers", "invoices"],
        "expected_operations": ["JOIN", "GROUP BY", "SUM", "COUNT"],
        "correct_sql": """
            SELECT e.FirstName || ' ' || e.LastName as EmployeeName,
                   COUNT(DISTINCT c.CustomerId) as TotalCustomers,
                   SUM(i.Total) as TotalRevenue
            FROM employees e
            JOIN customers c ON e.EmployeeId = c.SupportRepId
            JOIN invoices i ON c.CustomerId = i.CustomerId
            GROUP BY e.EmployeeId
            ORDER BY TotalRevenue DESC
        """
    },
    {
        "id": "M3",
        "description": "¿Cuáles son los 5 álbumes más vendidos (por cantidad de canciones vendidas)?",
        "expected_tables": ["albums", "tracks", "invoice_items"],
        "expected_operations": ["JOIN", "GROUP BY", "SUM", "ORDER BY", "LIMIT"],
        "correct_sql": """
            SELECT al.Title as Album,
                   ar.Name as Artist,
                   SUM(ii.Quantity) as TotalSold
            FROM albums al
            JOIN artists ar ON al.ArtistId = ar.ArtistId
            JOIN tracks t ON al.AlbumId = t.AlbumId
            JOIN invoice_items ii ON t.TrackId = ii.TrackId
            GROUP BY al.AlbumId
            ORDER BY TotalSold DESC
            LIMIT 5
        """
    },
    {
        "id": "M4",
        "description": "Calcula el ingreso total generado por cada género musical",
        "expected_tables": ["genres", "tracks", "invoice_items"],
        "expected_operations": ["JOIN", "GROUP BY", "SUM"],
        "correct_sql": """
            SELECT g.Name as Genre,
                   SUM(ii.UnitPrice * ii.Quantity) as TotalRevenue
            FROM genres g
            JOIN tracks t ON g.GenreId = t.GenreId
            JOIN invoice_items ii ON t.TrackId = ii.TrackId
            GROUP BY g.GenreId
            ORDER BY TotalRevenue DESC
        """
    },
    {
        "id": "M5",
        "description": "Muestra las ventas mensuales del año 2010 con su crecimiento mes a mes",
        "expected_tables": ["invoices"],
        "expected_operations": ["GROUP BY", "SUM", "strftime", "WHERE"],
        "correct_sql": """
            SELECT strftime('%Y-%m', InvoiceDate) as Month,
                   SUM(Total) as MonthlySales,
                   COUNT(InvoiceId) as TotalInvoices
            FROM invoices
            WHERE strftime('%Y', InvoiceDate) = '2010'
            GROUP BY Month
            ORDER BY Month
        """
    }
]

# ==============================================================================
# NIVEL AVANZADO (Dificultad 5/5)
# CTEs, subconsultas complejas, window functions, múltiples JOINs
# ==============================================================================

ADVANCED_TESTS = [
    {
        "id": "A1",
        "description": "Identifica los clientes que han gastado más que el promedio general y muestra cuánto más gastaron",
        "expected_tables": ["customers", "invoices"],
        "expected_operations": ["WITH/CTE", "JOIN", "GROUP BY", "HAVING", "subquery"],
        "correct_sql": """
            WITH CustomerSpending AS (
                SELECT c.CustomerId,
                       c.FirstName || ' ' || c.LastName as CustomerName,
                       SUM(i.Total) as TotalSpent
                FROM customers c
                JOIN invoices i ON c.CustomerId = i.CustomerId
                GROUP BY c.CustomerId
            ),
            AvgSpending AS (
                SELECT AVG(TotalSpent) as AvgTotal
                FROM CustomerSpending
            )
            SELECT cs.CustomerName,
                   ROUND(cs.TotalSpent, 2) as TotalSpent,
                   ROUND(a.AvgTotal, 2) as Average,
                   ROUND(cs.TotalSpent - a.AvgTotal, 2) as AboveAverage
            FROM CustomerSpending cs
            CROSS JOIN AvgSpending a
            WHERE cs.TotalSpent > a.AvgTotal
            ORDER BY AboveAverage DESC
        """
    },
    {
        "id": "A2",
        "description": "Para cada género, muestra el artista más vendido con el total de ventas y el porcentaje que representa del género",
        "expected_tables": ["genres", "artists", "albums", "tracks", "invoice_items"],
        "expected_operations": ["WITH/CTE", "JOIN", "GROUP BY", "ROW_NUMBER/MAX", "subquery"],
        "correct_sql": """
            WITH GenreArtistSales AS (
                SELECT g.Name as Genre,
                       ar.Name as Artist,
                       SUM(ii.UnitPrice * ii.Quantity) as ArtistRevenue
                FROM genres g
                JOIN tracks t ON g.GenreId = t.GenreId
                JOIN albums al ON t.AlbumId = al.AlbumId
                JOIN artists ar ON al.ArtistId = ar.ArtistId
                JOIN invoice_items ii ON t.TrackId = ii.TrackId
                GROUP BY g.GenreId, ar.ArtistId
            ),
            GenreTotals AS (
                SELECT Genre, SUM(ArtistRevenue) as GenreTotal
                FROM GenreArtistSales
                GROUP BY Genre
            ),
            RankedArtists AS (
                SELECT gas.Genre, 
                       gas.Artist, 
                       gas.ArtistRevenue,
                       gt.GenreTotal,
                       ROW_NUMBER() OVER (PARTITION BY gas.Genre ORDER BY gas.ArtistRevenue DESC) as Rank
                FROM GenreArtistSales gas
                JOIN GenreTotals gt ON gas.Genre = gt.Genre
            )
            SELECT Genre, 
                   Artist, 
                   ROUND(ArtistRevenue, 2) as Revenue,
                   ROUND((ArtistRevenue * 100.0 / GenreTotal), 2) as PercentageOfGenre
            FROM RankedArtists
            WHERE Rank = 1
            ORDER BY Revenue DESC
        """
    },
    {
        "id": "A3",
        "description": "Calcula la tasa de retención de clientes: cuántos clientes que compraron en 2009 también compraron en 2010",
        "expected_tables": ["invoices", "customers"],
        "expected_operations": ["WITH/CTE", "JOIN", "DISTINCT", "subquery", "COUNT"],
        "correct_sql": """
            WITH Customers2009 AS (
                SELECT DISTINCT CustomerId
                FROM invoices
                WHERE strftime('%Y', InvoiceDate) = '2009'
            ),
            Customers2010 AS (
                SELECT DISTINCT CustomerId
                FROM invoices
                WHERE strftime('%Y', InvoiceDate) = '2010'
            ),
            RetainedCustomers AS (
                SELECT c09.CustomerId
                FROM Customers2009 c09
                INNER JOIN Customers2010 c10 ON c09.CustomerId = c10.CustomerId
            )
            SELECT 
                (SELECT COUNT(*) FROM Customers2009) as Customers2009,
                (SELECT COUNT(*) FROM Customers2010) as Customers2010,
                (SELECT COUNT(*) FROM RetainedCustomers) as RetainedFromPrevYear,
                ROUND((SELECT COUNT(*) FROM RetainedCustomers) * 100.0 / 
                      (SELECT COUNT(*) FROM Customers2009), 2) as RetentionRate
        """
    },
    {
        "id": "A4",
        "description": "Análisis RFM: Segmenta a los clientes por Recency (última compra), Frequency (número de compras) y Monetary (total gastado)",
        "expected_tables": ["customers", "invoices"],
        "expected_operations": ["WITH/CTE", "JOIN", "GROUP BY", "CASE", "MAX", "COUNT", "SUM"],
        "correct_sql": """
            WITH CustomerRFM AS (
                SELECT c.CustomerId,
                       c.FirstName || ' ' || c.LastName as CustomerName,
                       julianday('2013-12-31') - julianday(MAX(i.InvoiceDate)) as DaysSinceLastPurchase,
                       COUNT(i.InvoiceId) as PurchaseFrequency,
                       SUM(i.Total) as TotalMonetary
                FROM customers c
                JOIN invoices i ON c.CustomerId = i.CustomerId
                GROUP BY c.CustomerId
            )
            SELECT CustomerName,
                   CAST(DaysSinceLastPurchase AS INTEGER) as Recency,
                   PurchaseFrequency as Frequency,
                   ROUND(TotalMonetary, 2) as Monetary,
                   CASE 
                       WHEN DaysSinceLastPurchase <= 90 AND PurchaseFrequency >= 7 AND TotalMonetary >= 40 
                       THEN 'VIP'
                       WHEN DaysSinceLastPurchase <= 180 AND PurchaseFrequency >= 5 
                       THEN 'Loyal'
                       WHEN DaysSinceLastPurchase <= 365 
                       THEN 'Active'
                       ELSE 'At Risk'
                   END as Segment
            FROM CustomerRFM
            ORDER BY Monetary DESC
        """
    },
    {
        "id": "A5",
        "description": "Encuentra las combinaciones de géneros más comunes en las playlists (qué géneros suelen estar juntos)",
        "expected_tables": ["playlists", "playlist_track", "tracks", "genres"],
        "expected_operations": ["WITH/CTE", "JOIN", "self-join", "GROUP BY", "HAVING"],
        "correct_sql": """
            WITH PlaylistGenres AS (
                SELECT DISTINCT p.PlaylistId,
                       p.Name as PlaylistName,
                       g.Name as Genre
                FROM playlists p
                JOIN playlist_track pt ON p.PlaylistId = pt.PlaylistId
                JOIN tracks t ON pt.TrackId = t.TrackId
                JOIN genres g ON t.GenreId = g.GenreId
            )
            SELECT pg1.Genre as Genre1,
                   pg2.Genre as Genre2,
                   COUNT(DISTINCT pg1.PlaylistId) as PlaylistsInCommon
            FROM PlaylistGenres pg1
            JOIN PlaylistGenres pg2 ON pg1.PlaylistId = pg2.PlaylistId 
                                    AND pg1.Genre < pg2.Genre
            GROUP BY pg1.Genre, pg2.Genre
            HAVING PlaylistsInCommon >= 3
            ORDER BY PlaylistsInCommon DESC
            LIMIT 10
        """
    }
]

# ==============================================================================
# CONJUNTO COMPLETO DE TESTS
# ==============================================================================

ALL_TESTS = {
    "basic": BASIC_TESTS,
    "medium": MEDIUM_TESTS,
    "advanced": ADVANCED_TESTS
}

def get_all_tests():
    """Retorna todos los tests en una lista plana"""
    return BASIC_TESTS + MEDIUM_TESTS + ADVANCED_TESTS

def get_tests_by_level(level: str):
    """Retorna tests de un nivel específico"""
    return ALL_TESTS.get(level.lower(), [])

def get_test_by_id(test_id: str):
    """Busca un test por su ID"""
    for test in get_all_tests():
        if test["id"] == test_id:
            return test
    return None
