const express = require("express");
const cors = require("cors");

const app = express();
const PORT = 3000;

// Middleware
app.use(cors());
app.use(express.json());

// Dummy endpoint untuk tes
app.get("/", (req, res) => {
  res.send("Volttrack backend is running 🚀");
});

// Endpoint login sederhana
app.post("/auth/login", (req, res) => {
  const { username, password } = req.body;

  if (username === "galapaksi81" && password === "123") {
    res.json({
      success: true,
      user: { username: "galapaksi81" }
    });
  } else {
    res.status(401).json({ success: false, message: "Login gagal" });
  }
});

// Contoh API dummy data energi
app.get("/api/energy", (req, res) => {
  res.json({
    power: "120 W",
    battery: "65%",
    voltage: "2.1 V",
    current: "0.57 A",
    efficiency: "78%"
  });
});

// Jalankan server
app.listen(PORT, () => {
  console.log(`Server running on http://localhost:${PORT}`);
});
