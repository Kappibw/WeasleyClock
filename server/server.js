require('dotenv').config();
const express = require('express');
const mysql = require('mysql');
const schedule = require('node-schedule');

const app = express();
const port = process.env.PORT || 3000;

const dbConfig = {
    host: 'mysql.thinkkappi.com',
    user: 'kappi',
    password: '&q$9pzmTGT8a9Z',
    database: 'weasley_clock'
};

const db = mysql.createConnection(dbConfig);

db.connect(err => {
    if (err) {
        console.error('Database connection error:', err);
    } else {
        console.log('Connected to the database');
    }
});

app.use(express.json());

// Authorization middleware function
const authorize = (req, res, next) => {
  const authHeader = req.headers.authorization;
  const correctToken = process.env.SECRET_TOKEN;  // Read from environment variable;

  if (!authHeader || authHeader !== correctToken) {
    res.status(401).send('Unauthorized');
  } else {
    next();
  }
};

// POST endpoint to insert data
app.post('/api.thinkkappi.com/update_location', (req, res) => {
    const { name, coordinates } = req.body;
    // Format the location as a MySQL POINT string
    const pointString = `ST_GeomFromText('${coordinates}')`;

    const sql = `INSERT INTO locations (name, coordinates, timestamp) VALUES (?, ${pointString}, NOW())`;
    
    db.query(sql, [name], (err, result) => {
        if (err) {
            console.error('Error inserting data:', err);
            res.status(500).json({ error: 'Internal server error' });
        } else {
            res.json({ message: 'Data inserted successfully' });
        }
    });
});

// GET endpoint to fetch data
app.get('/api.thinkkappi.com/get_locations', authorize, (req, res) => {
    const sql = `SELECT * FROM locations`;

    db.query(sql, (err, rows) => {
        if (err) {
            console.error('Error fetching data:', err);
            res.status(500).json({ error: 'Internal server error' });
        } else {
            res.json(rows);
        }
    });
});

// Schedule task to clear old entries every 10 minutes
const clearOldEntriesSchedule = schedule.scheduleJob('*/10 * * * *', () => {
    // Calculate the timestamp for one day ago
    const oneDayAgo = new Date(Date.now() - 24 * 60 * 60 * 1000).toISOString();

    const sql = `DELETE FROM locations WHERE timestamp < ?`;

    db.query(sql, [oneDayAgo], (err, result) => {
        if (err) {
            console.error('Error clearing old locations:', err);
        } else {
            const deletedCount = result.affectedRows;
	    console.log(`${deletedCount} old locations cleared`);
        }
    });
});


app.listen(port, () => {
    console.log(`Server listening on port ${port}`);
});

