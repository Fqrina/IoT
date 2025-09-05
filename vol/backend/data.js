const users = [
cod: 210, // mg/L
bod: 82, // mg/L
efficiency: 83, // % (efisiensi sistem)
energyStored: 1200, // Wh (kapasitas baterai terisi)
// Energi harian 7 hari (Wh)
energyGraph: [220, 250, 280, 310, 300, 270, 295],
// Pembacaan sensor (terbaru di akhir)
readings: [
{ t: "2025-08-29T08:00:00+07:00", voltage: 0.74, current: 0.31, ph: 6.7, temp: 28, cod: 220, bod: 85 },
{ t: "2025-08-30T08:00:00+07:00", voltage: 0.76, current: 0.33, ph: 6.8, temp: 28, cod: 215, bod: 83 },
{ t: "2025-08-31T08:00:00+07:00", voltage: 0.78, current: 0.34, ph: 6.8, temp: 28, cod: 210, bod: 82 },
],
},
{
id: 2,
name: "Sungai Bengawan Solo",
voltage: 0.82,
current: 0.29,
power: 0.82 * 0.29,
ph: 7.1,
temperature: 29,
cod: 185,
bod: 74,
efficiency: 85,
energyStored: 980,
energyGraph: [200, 210, 240, 260, 255, 235, 245],
readings: [
{ t: "2025-08-29T08:00:00+07:00", voltage: 0.79, current: 0.27, ph: 7.0, temp: 29, cod: 195, bod: 76 },
{ t: "2025-08-30T08:00:00+07:00", voltage: 0.81, current: 0.28, ph: 7.1, temp: 29, cod: 190, bod: 75 },
{ t: "2025-08-31T08:00:00+07:00", voltage: 0.82, current: 0.29, ph: 7.1, temp: 29, cod: 185, bod: 74 },
],
},
{
id: 3,
name: "Sungai Kapuas",
voltage: 0.69,
current: 0.31,
power: 0.69 * 0.31,
ph: 6.5,
temperature: 27,
cod: 230,
bod: 90,
efficiency: 79,
energyStored: 760,
energyGraph: [180, 190, 210, 220, 215, 205, 210],
readings: [
{ t: "2025-08-29T08:00:00+07:00", voltage: 0.65, current: 0.29, ph: 6.4, temp: 27, cod: 240, bod: 95 },
{ t: "2025-08-30T08:00:00+07:00", voltage: 0.67, current: 0.30, ph: 6.5, temp: 27, cod: 235, bod: 92 },
{ t: "2025-08-31T08:00:00+07:00", voltage: 0.69, current: 0.31, ph: 6.5, temp: 27, cod: 230, bod: 90 },
],
},
];


const feedbacks = [];


module.exports = { users, rivers, feedbacks };