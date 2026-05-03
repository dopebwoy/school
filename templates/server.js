const express = require('express');
const fs = require('fs');
const app = express();

app.use(express.json()); // Allows server to read JSON from your button
app.use(express.static('.')); // Serves your HTML file

app.post('/api/save_db', (req, res) => {
    const data = req.body;
    
    // Save the data sent from your HTML to a local file
    fs.writeFile('database.json', JSON.stringify(data, null, 2), (err) => {
        if (err) {
            return res.status(500).send("Error saving data");
        }
        res.status(200).send("Database Initialized");
    });
});

app.listen(3000, () => console.log('Server running on port 3000'));
