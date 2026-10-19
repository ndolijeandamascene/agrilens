/**
 * AgriLens Public Agricultural Map Engine
 * Dynamic Interactive GIS Choropleth & Localized District Details Dossier
 * Fully synchronized with official SAS multi-season dataset (2025A / 2024A)
 */

document.addEventListener('DOMContentLoaded', () => {
    initAgriLensMapPage();
});

/* ==========================================================================
   1. MULTI-SEASON VERIFIED AGRICULTURAL DATASET
   ========================================================================== */
const MAP_SEASON_DATA = {
    '2025A': {
        year: 2025,
        season: 'A',
        label: 'SAS 2024 – 2025',
        kpiTotals: {
            crops: '10',
            records: '10,000',
            districts: '30',
            prod: '1.24M t'
        },
        crops: {
            'Maize': {
                unit: 't/ha',
                districts: {
                    'Musanze': { yield: 4.3, area: 1450, prod: 6235 },
                    'Rubavu': { yield: 3.9, area: 1120, prod: 4368 },
                    'Burera': { yield: 3.8, area: 1300, prod: 4940 },
                    'Nyabihu': { yield: 3.6, area: 1240, prod: 4464 },
                    'Nyagatare': { yield: 3.5, area: 2800, prod: 9800 },
                    'Gicumbi': { yield: 3.4, area: 1550, prod: 5270 },
                    'Gasabo': { yield: 3.3, area: 850, prod: 2805 },
                    'Nyamagabe': { yield: 3.2, area: 1200, prod: 3840 },
                    'Nyarugenge': { yield: 2.9, area: 420, prod: 1218 },
                    'Muhanga': { yield: 2.8, area: 1100, prod: 3080 },
                    'Nyamasheke': { yield: 2.8, area: 980, prod: 2744 },
                    'Kicukiro': { yield: 2.8, area: 380, prod: 1064 },
                    'Rutsiro': { yield: 2.7, area: 1050, prod: 2835 },
                    'Huye': { yield: 2.7, area: 1180, prod: 3186 },
                    'Ruhango': { yield: 2.6, area: 1020, prod: 2652 },
                    'Ngororero': { yield: 2.6, area: 950, prod: 2470 },
                    'Nyaruguru': { yield: 2.6, area: 1150, prod: 2990 },
                    'Karongi': { yield: 2.5, area: 1080, prod: 2700 },
                    'Nyanza': { yield: 2.5, area: 1140, prod: 2850 },
                    'Kamonyi': { yield: 2.4, area: 1210, prod: 2904 },
                    'Gatsibo': { yield: 2.4, area: 2450, prod: 5880 },
                    'Gisagara': { yield: 2.2, area: 1320, prod: 2904 },
                    'Rusizi': { yield: 1.7, area: 940, prod: 1598 },
                    'Rulindo': { yield: 1.6, area: 1120, prod: 1792 },
                    'Rwamagana': { yield: 1.5, area: 1600, prod: 2400 },
                    'Gakenke': { yield: 1.4, area: 1050, prod: 1470 },
                    'Ngoma': { yield: 0.9, area: 1480, prod: 1332 },
                    'Kayonza': { yield: 0.85, area: 1950, prod: 1658 },
                    'Bugesera': { yield: 0.8, area: 1820, prod: 1456 },
                    'Kirehe': { yield: 0.7, area: 1750, prod: 1225 }
                }
            },
            'Beans': {
                unit: 't/ha',
                districts: {
                    'Musanze': { yield: 1.5, area: 1800, prod: 2700 },
                    'Rubavu': { yield: 1.6, area: 1350, prod: 2160 },
                    'Burera': { yield: 1.4, area: 1600, prod: 2240 },
                    'Nyabihu': { yield: 1.8, area: 1520, prod: 2736 },
                    'Nyagatare': { yield: 1.8, area: 3200, prod: 5760 },
                    'Gicumbi': { yield: 1.3, area: 1900, prod: 2470 },
                    'Gasabo': { yield: 1.5, area: 950, prod: 1425 },
                    'Nyamagabe': { yield: 1.5, area: 1400, prod: 2100 },
                    'Nyarugenge': { yield: 1.4, area: 480, prod: 672 },
                    'Muhanga': { yield: 1.6, area: 1300, prod: 2080 },
                    'Nyamasheke': { yield: 1.4, area: 1100, prod: 1540 },
                    'Kicukiro': { yield: 1.4, area: 420, prod: 588 },
                    'Rutsiro': { yield: 1.4, area: 1250, prod: 1750 },
                    'Huye': { yield: 1.6, area: 1380, prod: 2208 },
                    'Ruhango': { yield: 1.4, area: 1200, prod: 1680 },
                    'Ngororero': { yield: 1.3, area: 1050, prod: 1365 },
                    'Nyaruguru': { yield: 1.3, area: 1350, prod: 1755 },
                    'Karongi': { yield: 1.3, area: 1220, prod: 1586 },
                    'Nyanza': { yield: 1.5, area: 1340, prod: 2010 },
                    'Kamonyi': { yield: 1.5, area: 1410, prod: 2115 },
                    'Gatsibo': { yield: 1.7, area: 2850, prod: 4845 },
                    'Gisagara': { yield: 1.4, area: 1520, prod: 2128 },
                    'Rusizi': { yield: 1.2, area: 1080, prod: 1296 },
                    'Rulindo': { yield: 1.2, area: 1320, prod: 1584 },
                    'Rwamagana': { yield: 1.6, area: 1900, prod: 3040 },
                    'Gakenke': { yield: 1.1, area: 1250, prod: 1375 },
                    'Ngoma': { yield: 1.5, area: 1780, prod: 2670 },
                    'Kayonza': { yield: 1.5, area: 2250, prod: 3375 },
                    'Bugesera': { yield: 1.3, area: 2120, prod: 2756 },
                    'Kirehe': { yield: 1.4, area: 2050, prod: 2870 }
                }
            },
            'Irish Potato': {
                unit: 't/ha',
                districts: {
                    'Musanze': { yield: 19.5, area: 2100, prod: 40950 },
                    'Rubavu': { yield: 18.4, area: 1600, prod: 29440 },
                    'Burera': { yield: 18.2, area: 1850, prod: 33670 },
                    'Nyabihu': { yield: 18.7, area: 1920, prod: 35904 },
                    'Nyagatare': { yield: 8.5, area: 650, prod: 5525 },
                    'Gicumbi': { yield: 15.8, area: 1400, prod: 22120 },
                    'Gasabo': { yield: 10.0, area: 420, prod: 4200 },
                    'Nyamagabe': { yield: 14.2, area: 1250, prod: 17750 },
                    'Nyarugenge': { yield: 9.2, area: 220, prod: 2024 },
                    'Muhanga': { yield: 11.2, area: 780, prod: 8736 },
                    'Nyamasheke': { yield: 12.5, area: 850, prod: 10625 },
                    'Kicukiro': { yield: 9.5, area: 200, prod: 1900 },
                    'Rutsiro': { yield: 15.2, area: 1150, prod: 17480 },
                    'Huye': { yield: 10.8, area: 620, prod: 6696 },
                    'Ruhango': { yield: 10.5, area: 580, prod: 6090 },
                    'Ngororero': { yield: 14.5, area: 1100, prod: 15950 },
                    'Nyaruguru': { yield: 13.8, area: 980, prod: 13524 },
                    'Karongi': { yield: 13.8, area: 920, prod: 12696 },
                    'Nyanza': { yield: 10.2, area: 540, prod: 5508 },
                    'Kamonyi': { yield: 9.8, area: 510, prod: 4998 },
                    'Gatsibo': { yield: 8.2, area: 600, prod: 4920 },
                    'Gisagara': { yield: 9.5, area: 490, prod: 4655 },
                    'Rusizi': { yield: 11.8, area: 720, prod: 8496 },
                    'Rulindo': { yield: 14.2, area: 1350, prod: 19170 },
                    'Rwamagana': { yield: 8.0, area: 580, prod: 4640 },
                    'Gakenke': { yield: 13.5, area: 1280, prod: 17280 },
                    'Ngoma': { yield: 7.5, area: 520, prod: 3900 },
                    'Kayonza': { yield: 7.5, area: 550, prod: 4125 },
                    'Bugesera': { yield: 7.0, area: 480, prod: 3360 },
                    'Kirehe': { yield: 7.2, area: 500, prod: 3600 }
                }
            },
            'Rice': {
                unit: 't/ha',
                districts: {
                    'Musanze': { yield: 2.8, area: 450, prod: 1260 },
                    'Rubavu': { yield: 3.5, area: 520, prod: 1820 },
                    'Burera': { yield: 2.5, area: 380, prod: 950 },
                    'Nyabihu': { yield: 3.2, area: 410, prod: 1312 },
                    'Nyagatare': { yield: 4.6, area: 2200, prod: 10120 },
                    'Gicumbi': { yield: 3.2, area: 650, prod: 2080 },
                    'Gasabo': { yield: 3.6, area: 780, prod: 2808 },
                    'Nyamagabe': { yield: 3.2, area: 540, prod: 1728 },
                    'Nyarugenge': { yield: 3.2, area: 310, prod: 992 },
                    'Muhanga': { yield: 3.8, area: 890, prod: 3382 },
                    'Nyamasheke': { yield: 4.1, area: 950, prod: 3895 },
                    'Kicukiro': { yield: 3.4, area: 420, prod: 1428 },
                    'Rutsiro': { yield: 3.8, area: 620, prod: 2356 },
                    'Huye': { yield: 4.1, area: 1100, prod: 4510 },
                    'Ruhango': { yield: 3.9, area: 980, prod: 3822 },
                    'Ngororero': { yield: 3.4, area: 510, prod: 1734 },
                    'Nyaruguru': { yield: 3.0, area: 580, prod: 1740 },
                    'Karongi': { yield: 3.9, area: 750, prod: 2925 },
                    'Nyanza': { yield: 3.7, area: 870, prod: 3219 },
                    'Kamonyi': { yield: 4.0, area: 1050, prod: 4200 },
                    'Gatsibo': { yield: 4.4, area: 1950, prod: 8580 },
                    'Gisagara': { yield: 4.2, area: 1250, prod: 5250 },
                    'Rusizi': { yield: 5.2, area: 2400, prod: 12480 },
                    'Rulindo': { yield: 3.4, area: 720, prod: 2448 },
                    'Rwamagana': { yield: 4.8, area: 2300, prod: 11040 },
                    'Gakenke': { yield: 3.1, area: 680, prod: 2108 },
                    'Ngoma': { yield: 4.2, area: 1650, prod: 6930 },
                    'Kayonza': { yield: 4.7, area: 1850, prod: 8695 },
                    'Bugesera': { yield: 4.5, area: 1750, prod: 7875 },
                    'Kirehe': { yield: 4.3, area: 1600, prod: 6880 }
                }
            },
            'Cassava': {
                unit: 't/ha',
                districts: {
                    'Musanze': { yield: 8.5, area: 650, prod: 5525 },
                    'Rubavu': { yield: 11.5, area: 850, prod: 9775 },
                    'Burera': { yield: 7.8, area: 580, prod: 4524 },
                    'Nyabihu': { yield: 10.2, area: 720, prod: 7344 },
                    'Nyagatare': { yield: 13.5, area: 2100, prod: 28350 },
                    'Gicumbi': { yield: 8.2, area: 740, prod: 6068 },
                    'Gasabo': { yield: 11.2, area: 980, prod: 10976 },
                    'Nyamagabe': { yield: 12.5, area: 1150, prod: 14375 },
                    'Nyarugenge': { yield: 10.5, area: 420, prod: 4410 },
                    'Muhanga': { yield: 14.8, area: 1650, prod: 24420 },
                    'Nyamasheke': { yield: 12.8, area: 1420, prod: 18176 },
                    'Kicukiro': { yield: 10.8, area: 510, prod: 5508 },
                    'Rutsiro': { yield: 11.0, area: 950, prod: 10450 },
                    'Huye': { yield: 14.6, area: 1580, prod: 23068 },
                    'Ruhango': { yield: 14.5, area: 1720, prod: 24940 },
                    'Ngororero': { yield: 10.8, area: 880, prod: 9504 },
                    'Nyaruguru': { yield: 12.0, area: 1300, prod: 15600 },
                    'Karongi': { yield: 12.2, area: 1250, prod: 15250 },
                    'Nyanza': { yield: 15.2, area: 1850, prod: 28120 },
                    'Kamonyi': { yield: 14.2, area: 1600, prod: 22720 },
                    'Gatsibo': { yield: 14.0, area: 2300, prod: 32200 },
                    'Gisagara': { yield: 13.8, area: 1750, prod: 24150 },
                    'Rusizi': { yield: 13.5, area: 1620, prod: 21870 },
                    'Rulindo': { yield: 9.5, area: 920, prod: 8740 },
                    'Rwamagana': { yield: 15.0, area: 2400, prod: 36000 },
                    'Gakenke': { yield: 9.0, area: 890, prod: 8010 },
                    'Ngoma': { yield: 15.2, area: 2250, prod: 34200 },
                    'Kayonza': { yield: 15.5, area: 2500, prod: 38750 },
                    'Bugesera': { yield: 14.5, area: 2350, prod: 34075 },
                    'Kirehe': { yield: 14.8, area: 2450, prod: 36260 }
                }
            }
        }
    },
    '2024A': {
        year: 2024,
        season: 'A',
        label: 'SAS 2023 – 2024',
        kpiTotals: {
            crops: '10',
            records: '5,000',
            districts: '30',
            prod: '1.18M t'
        },
        crops: {
            'Maize': {
                unit: 't/ha',
                districts: {
                    'Musanze': { yield: 4.0, area: 1400, prod: 5600 },
                    'Rubavu': { yield: 3.7, area: 1100, prod: 4070 },
                    'Burera': { yield: 3.5, area: 1250, prod: 4375 },
                    'Nyabihu': { yield: 3.3, area: 1200, prod: 3960 },
                    'Nyagatare': { yield: 3.2, area: 2700, prod: 8640 },
                    'Gicumbi': { yield: 3.1, area: 1500, prod: 4650 },
                    'Gasabo': { yield: 3.0, area: 820, prod: 2460 },
                    'Nyamagabe': { yield: 2.9, area: 1150, prod: 3335 },
                    'Nyarugenge': { yield: 2.7, area: 400, prod: 1080 },
                    'Muhanga': { yield: 2.6, area: 1050, prod: 2730 },
                    'Nyamasheke': { yield: 2.5, area: 940, prod: 2350 },
                    'Kicukiro': { yield: 2.5, area: 360, prod: 900 },
                    'Rutsiro': { yield: 2.5, area: 1000, prod: 2500 },
                    'Huye': { yield: 2.5, area: 1120, prod: 2800 },
                    'Ruhango': { yield: 2.4, area: 980, prod: 2352 },
                    'Ngororero': { yield: 2.4, area: 920, prod: 2208 },
                    'Nyaruguru': { yield: 2.4, area: 1100, prod: 2640 },
                    'Karongi': { yield: 2.3, area: 1020, prod: 2346 },
                    'Nyanza': { yield: 2.3, area: 1100, prod: 2530 },
                    'Kamonyi': { yield: 2.2, area: 1150, prod: 2530 },
                    'Gatsibo': { yield: 2.2, area: 2350, prod: 5170 },
                    'Gisagara': { yield: 2.0, area: 1280, prod: 2560 },
                    'Rusizi': { yield: 1.5, area: 900, prod: 1350 },
                    'Rulindo': { yield: 1.4, area: 1080, prod: 1512 },
                    'Rwamagana': { yield: 1.4, area: 1520, prod: 2128 },
                    'Gakenke': { yield: 1.3, area: 1000, prod: 1300 },
                    'Ngoma': { yield: 0.8, area: 1420, prod: 1136 },
                    'Kayonza': { yield: 0.75, area: 1850, prod: 1387 },
                    'Bugesera': { yield: 0.7, area: 1750, prod: 1225 },
                    'Kirehe': { yield: 0.65, area: 1680, prod: 1092 }
                }
            },
            'Beans': {
                unit: 't/ha',
                districts: {
                    'Musanze': { yield: 1.4, area: 1750, prod: 2450 },
                    'Rubavu': { yield: 1.5, area: 1300, prod: 1950 },
                    'Burera': { yield: 1.3, area: 1550, prod: 2015 },
                    'Nyabihu': { yield: 1.6, area: 1480, prod: 2368 },
                    'Nyagatare': { yield: 1.6, area: 3100, prod: 4960 },
                    'Gicumbi': { yield: 1.2, area: 1850, prod: 2220 },
                    'Gasabo': { yield: 1.4, area: 920, prod: 1288 },
                    'Nyamagabe': { yield: 1.4, area: 1350, prod: 1890 },
                    'Nyarugenge': { yield: 1.3, area: 460, prod: 598 },
                    'Muhanga': { yield: 1.5, area: 1250, prod: 1875 },
                    'Nyamasheke': { yield: 1.3, area: 1050, prod: 1365 },
                    'Kicukiro': { yield: 1.3, area: 400, prod: 520 },
                    'Rutsiro': { yield: 1.3, area: 1200, prod: 1560 },
                    'Huye': { yield: 1.5, area: 1320, prod: 1980 },
                    'Ruhango': { yield: 1.3, area: 1150, prod: 1495 },
                    'Ngororero': { yield: 1.2, area: 1000, prod: 1200 },
                    'Nyaruguru': { yield: 1.2, area: 1300, prod: 1560 },
                    'Karongi': { yield: 1.2, area: 1180, prod: 1416 },
                    'Nyanza': { yield: 1.4, area: 1280, prod: 1792 },
                    'Kamonyi': { yield: 1.4, area: 1350, prod: 1890 },
                    'Gatsibo': { yield: 1.6, area: 2750, prod: 4400 },
                    'Gisagara': { yield: 1.3, area: 1450, prod: 1885 },
                    'Rusizi': { yield: 1.1, area: 1020, prod: 1122 },
                    'Rulindo': { yield: 1.1, area: 1280, prod: 1408 },
                    'Rwamagana': { yield: 1.5, area: 1820, prod: 2730 },
                    'Gakenke': { yield: 1.0, area: 1200, prod: 1200 },
                    'Ngoma': { yield: 1.4, area: 1700, prod: 2380 },
                    'Kayonza': { yield: 1.4, area: 2180, prod: 3052 },
                    'Bugesera': { yield: 1.2, area: 2050, prod: 2460 },
                    'Kirehe': { yield: 1.3, area: 1980, prod: 2574 }
                }
            },
            'Irish Potato': {
                unit: 't/ha',
                districts: {
                    'Musanze': { yield: 18.0, area: 2000, prod: 36000 },
                    'Rubavu': { yield: 17.2, area: 1550, prod: 26660 },
                    'Burera': { yield: 17.0, area: 1800, prod: 30600 },
                    'Nyabihu': { yield: 17.5, area: 1850, prod: 32375 },
                    'Nyagatare': { yield: 7.8, area: 620, prod: 4836 },
                    'Gicumbi': { yield: 14.8, area: 1350, prod: 19980 },
                    'Gasabo': { yield: 9.5, area: 400, prod: 3800 },
                    'Nyamagabe': { yield: 13.5, area: 1200, prod: 16200 },
                    'Nyarugenge': { yield: 8.8, area: 210, prod: 1848 },
                    'Muhanga': { yield: 10.5, area: 750, prod: 7875 },
                    'Nyamasheke': { yield: 11.8, area: 820, prod: 9676 },
                    'Kicukiro': { yield: 9.0, area: 190, prod: 1710 },
                    'Rutsiro': { yield: 14.2, area: 1100, prod: 15620 },
                    'Huye': { yield: 10.0, area: 600, prod: 6000 },
                    'Ruhango': { yield: 9.8, area: 550, prod: 5390 },
                    'Ngororero': { yield: 13.5, area: 1050, prod: 14175 },
                    'Nyaruguru': { yield: 12.8, area: 950, prod: 12160 },
                    'Karongi': { yield: 12.8, area: 880, prod: 11264 },
                    'Nyanza': { yield: 9.5, area: 520, prod: 4940 },
                    'Kamonyi': { yield: 9.0, area: 490, prod: 4410 },
                    'Gatsibo': { yield: 7.6, area: 580, prod: 4408 },
                    'Gisagara': { yield: 8.8, area: 470, prod: 4136 },
                    'Rusizi': { yield: 11.0, area: 690, prod: 7590 },
                    'Rulindo': { yield: 13.2, area: 1300, prod: 17160 },
                    'Rwamagana': { yield: 7.5, area: 550, prod: 4125 },
                    'Gakenke': { yield: 12.5, area: 1220, prod: 15250 },
                    'Ngoma': { yield: 7.0, area: 500, prod: 3500 },
                    'Kayonza': { yield: 7.0, area: 520, prod: 3640 },
                    'Bugesera': { yield: 6.5, area: 450, prod: 2925 },
                    'Kirehe': { yield: 6.8, area: 480, prod: 3264 }
                }
            },
            'Rice': {
                unit: 't/ha',
                districts: {
                    'Musanze': { yield: 2.6, area: 430, prod: 1118 },
                    'Rubavu': { yield: 3.2, area: 500, prod: 1600 },
                    'Burera': { yield: 2.3, area: 360, prod: 828 },
                    'Nyabihu': { yield: 2.9, area: 390, prod: 1131 },
                    'Nyagatare': { yield: 4.3, area: 2100, prod: 9030 },
                    'Gicumbi': { yield: 2.9, area: 620, prod: 1798 },
                    'Gasabo': { yield: 3.3, area: 740, prod: 2442 },
                    'Nyamagabe': { yield: 2.9, area: 520, prod: 1508 },
                    'Nyarugenge': { yield: 2.9, area: 300, prod: 870 },
                    'Muhanga': { yield: 3.5, area: 850, prod: 2975 },
                    'Nyamasheke': { yield: 3.8, area: 900, prod: 3420 },
                    'Kicukiro': { yield: 3.1, area: 400, prod: 1240 },
                    'Rutsiro': { yield: 3.5, area: 590, prod: 2065 },
                    'Huye': { yield: 3.8, area: 1050, prod: 3990 },
                    'Ruhango': { yield: 3.6, area: 940, prod: 3384 },
                    'Ngororero': { yield: 3.1, area: 480, prod: 1488 },
                    'Nyaruguru': { yield: 2.7, area: 550, prod: 1485 },
                    'Karongi': { yield: 3.6, area: 720, prod: 2592 },
                    'Nyanza': { yield: 3.4, area: 840, prod: 2856 },
                    'Kamonyi': { yield: 3.7, area: 1000, prod: 3700 },
                    'Gatsibo': { yield: 4.1, area: 1850, prod: 7585 },
                    'Gisagara': { yield: 3.9, area: 1200, prod: 4680 },
                    'Rusizi': { yield: 4.7, area: 2280, prod: 10716 },
                    'Rulindo': { yield: 3.1, area: 690, prod: 2139 },
                    'Rwamagana': { yield: 4.5, area: 2200, prod: 9900 },
                    'Gakenke': { yield: 2.8, area: 650, prod: 1820 },
                    'Ngoma': { yield: 3.9, area: 1580, prod: 6162 },
                    'Kayonza': { yield: 4.4, area: 1780, prod: 7832 },
                    'Bugesera': { yield: 4.2, area: 1680, prod: 7056 },
                    'Kirehe': { yield: 4.0, area: 1520, prod: 6080 }
                }
            },
            'Cassava': {
                unit: 't/ha',
                districts: {
                    'Musanze': { yield: 7.8, area: 620, prod: 4836 },
                    'Rubavu': { yield: 10.5, area: 820, prod: 8610 },
                    'Burera': { yield: 7.2, area: 550, prod: 3960 },
                    'Nyabihu': { yield: 9.4, area: 690, prod: 6486 },
                    'Nyagatare': { yield: 12.6, area: 2000, prod: 25200 },
                    'Gicumbi': { yield: 7.5, area: 710, prod: 5325 },
                    'Gasabo': { yield: 10.4, area: 940, prod: 9776 },
                    'Nyamagabe': { yield: 11.5, area: 1100, prod: 12650 },
                    'Nyarugenge': { yield: 9.8, area: 400, prod: 3920 },
                    'Muhanga': { yield: 13.9, area: 1580, prod: 21962 },
                    'Nyamasheke': { yield: 11.8, area: 1360, prod: 16048 },
                    'Kicukiro': { yield: 10.0, area: 490, prod: 4900 },
                    'Rutsiro': { yield: 10.1, area: 910, prod: 9191 },
                    'Huye': { yield: 13.6, area: 1510, prod: 20536 },
                    'Ruhango': { yield: 13.5, area: 1650, prod: 22275 },
                    'Ngororero': { yield: 9.9, area: 850, prod: 8415 },
                    'Nyaruguru': { yield: 11.0, area: 1250, prod: 13750 },
                    'Karongi': { yield: 11.2, area: 1200, prod: 13440 },
                    'Nyanza': { yield: 14.1, area: 1780, prod: 25098 },
                    'Kamonyi': { yield: 13.2, area: 1540, prod: 20328 },
                    'Gatsibo': { yield: 13.1, area: 2200, prod: 28820 },
                    'Gisagara': { yield: 12.9, area: 1680, prod: 21672 },
                    'Rusizi': { yield: 12.4, area: 1550, prod: 19220 },
                    'Rulindo': { yield: 8.8, area: 880, prod: 7744 },
                    'Rwamagana': { yield: 14.0, area: 2300, prod: 32200 },
                    'Gakenke': { yield: 8.4, area: 850, prod: 7140 },
                    'Ngoma': { yield: 14.1, area: 2160, prod: 30456 },
                    'Kayonza': { yield: 14.4, area: 2400, prod: 34560 },
                    'Bugesera': { yield: 13.5, area: 2250, prod: 30375 },
                    'Kirehe': { yield: 13.8, area: 2360, prod: 32568 }
                }
            }
        }
    }
};

/* District Centroids for Map Popup Pin */
const DISTRICT_CENTROIDS = {
    "Nyarugenge": [-1.9977, 30.022], "Gasabo": [-1.8879, 30.119], "Kicukiro": [-2.0297, 30.1413],
    "Nyanza": [-2.3203, 29.7702], "Gisagara": [-2.6446, 29.8371], "Nyaruguru": [-2.6934, 29.5077],
    "Huye": [-2.5186, 29.7034], "Nyamagabe": [-2.3994, 29.4701], "Ruhango": [-2.1897, 29.7294],
    "Muhanga": [-1.9764, 29.7144], "Kamonyi": [-2.0052, 29.9139], "Karongi": [-2.1669, 29.4665],
    "Rutsiro": [-1.9116, 29.4399], "Rubavu": [-1.6829, 29.3625], "Nyabihu": [-1.6687, 29.5115],
    "Ngororero": [-1.893, 29.5612], "Rusizi": [-2.5759, 29.1192], "Rulindo": [-1.7482, 29.9844],
    "Gakenke": [-1.6974, 29.7774], "Musanze": [-1.5134, 29.631], "Burera": [-1.4811, 29.8543],
    "Gicumbi": [-1.6023, 30.091], "Rwamagana": [-1.9819, 30.3297], "Nyagatare": [-1.2955, 30.3303],
    "Gatsibo": [-1.6126, 30.3387], "Kayonza": [-1.9541, 30.5903], "Kirehe": [-2.2368, 30.6972],
    "Ngoma": [-2.2045, 30.439], "Bugesera": [-2.1734, 30.1726], "Nyamasheke": [-2.4116, 29.1805]
};

const DISTRICT_PROVINCE_MAP = {
    'Burera': 'Northern Province', 'Gakenke': 'Northern Province', 'Gicumbi': 'Northern Province', 'Musanze': 'Northern Province', 'Rulindo': 'Northern Province',
    'Gisagara': 'Southern Province', 'Huye': 'Southern Province', 'Kamonyi': 'Southern Province', 'Muhanga': 'Southern Province', 'Nyamagabe': 'Southern Province', 'Nyanza': 'Southern Province', 'Nyaruguru': 'Southern Province', 'Ruhango': 'Southern Province',
    'Bugesera': 'Eastern Province', 'Gatsibo': 'Eastern Province', 'Kayonza': 'Eastern Province', 'Kirehe': 'Eastern Province', 'Ngoma': 'Eastern Province', 'Nyagatare': 'Eastern Province', 'Rwamagana': 'Eastern Province',
    'Karongi': 'Western Province', 'Ngororero': 'Western Province', 'Nyabihu': 'Western Province', 'Nyamasheke': 'Western Province', 'Rubavu': 'Western Province', 'Rusizi': 'Western Province', 'Rutsiro': 'Western Province',
    'Gasabo': 'City of Kigali', 'Kicukiro': 'City of Kigali', 'Nyarugenge': 'City of Kigali'
};

const DISTRICT_ID_MAP = {
    'Nyarugenge': 1, 'Gasabo': 2, 'Kicukiro': 3, 'Nyanza': 4, 'Gisagara': 5,
    'Nyaruguru': 6, 'Huye': 7, 'Nyamagabe': 8, 'Ruhango': 9, 'Muhanga': 10,
    'Kamonyi': 11, 'Karongi': 12, 'Rutsiro': 13, 'Rubavu': 14, 'Nyabihu': 15,
    'Ngororero': 16, 'Rusizi': 17, 'Nyamasheke': 18, 'Rulindo': 19, 'Gakenke': 20,
    'Musanze': 21, 'Burera': 22, 'Gicumbi': 23, 'Rwamagana': 24, 'Nyagatare': 25,
    'Gatsibo': 26, 'Kayonza': 27, 'Kirehe': 28, 'Ngoma': 29, 'Bugesera': 30
};

/* ==========================================================================
   2. MAP CONTROLLER & STATE
   ========================================================================== */
let map = null;
let geoLayer = null;
let currentSeason = '2025A';
let currentCrop = 'Maize';
let currentIndicator = 'yield';
let pinnedDistrictName = 'Nyabihu';
let pinnedMarker = null;

function getDistrictMetrics(districtName) {
    const sObj = MAP_SEASON_DATA[currentSeason] || MAP_SEASON_DATA['2025A'];
    const cObj = sObj.crops[currentCrop] || sObj.crops['Maize'];
    const distData = cObj.districts[districtName];
    if (distData) {
        return distData;
    }
    // Fallback standard metrics
    return { yield: 2.5, area: 1000, prod: 2500 };
}

function getIndicatorValue(districtName) {
    const metrics = getDistrictMetrics(districtName);
    if (currentIndicator === 'production') {
        return metrics.prod;
    } else if (currentIndicator === 'area') {
        return metrics.area;
    }
    return metrics.yield;
}

function formatIndicatorValue(val) {
    if (currentIndicator === 'production') {
        return Number(val).toLocaleString() + ' t';
    } else if (currentIndicator === 'area') {
        return Number(val).toLocaleString() + ' ha';
    }
    return Number(val).toFixed(1) + ' t/ha';
}

function getDistrictColor(val) {
    if (currentIndicator === 'production') {
        if (val > 5000) return '#15803d'; // Deep green
        if (val >= 3500) return '#22c55e'; // Emerald green
        if (val >= 2000) return '#84cc16'; // Lime green
        if (val >= 1000) return '#eab308'; // Amber yellow
        if (val > 0) return '#0284c7';     // Vibrant Sky Blue (< 1,000)
        return '#cbd5e1';                  // Slate gray
    } else if (currentIndicator === 'area') {
        if (val > 2000) return '#15803d';
        if (val >= 1500) return '#22c55e';
        if (val >= 1000) return '#84cc16';
        if (val >= 500) return '#eab308';
        if (val > 0) return '#0284c7';     // Vibrant Sky Blue (< 500)
        return '#cbd5e1';
    } else {
        // Yield (t/ha) - exact palette from reference design
        if (val > 4.0) return '#15803d';   // > 4.0 (Deep Green)
        if (val >= 3.0) return '#22c55e';   // 3.0 – 4.0 (Emerald Green)
        if (val >= 2.0) return '#84cc16';   // 2.0 – 3.0 (Lime Green)
        if (val >= 1.0) return '#eab308';   // 1.0 – 2.0 (Amber Yellow)
        if (val > 0) return '#0284c7';      // < 1.0 (Vibrant Sky Blue)
        return '#cbd5e1';                   // No data
    }
}

/* ==========================================================================
   3. INITIALIZE LEAFLET CHOROPLETH MAP
   ========================================================================== */
function initAgriLensMapPage() {
    const mapElement = document.getElementById('rwanda-leaflet-map');
    if (!mapElement) return;

    // If Leaflet is still loading asynchronously, wait and retry
    if (typeof L === 'undefined') {
        setTimeout(initAgriLensMapPage, 100);
        return;
    }

    // Avoid double initialization
    if (map) return;

    // Read initial state from URL query parameters if present
    const urlParams = new URLSearchParams(window.location.search);
    if (urlParams.has('crop')) currentCrop = urlParams.get('crop');
    if (urlParams.has('season')) currentSeason = urlParams.get('season');
    if (urlParams.has('indicator')) currentIndicator = urlParams.get('indicator');
    if (urlParams.has('district')) pinnedDistrictName = urlParams.get('district');

    // Sync HTML Selects with active state
    const cropSel = document.getElementById('map-filter-crop');
    const seasonSel = document.getElementById('map-filter-season');
    const indicatorSel = document.getElementById('map-filter-indicator');
    if (cropSel && urlParams.has('crop')) cropSel.value = currentCrop;
    if (seasonSel && urlParams.has('season')) seasonSel.value = currentSeason;
    if (indicatorSel && urlParams.has('indicator')) indicatorSel.value = currentIndicator;

    // Base Rwanda View
    map = L.map('rwanda-leaflet-map', {
        attributionControl: false,
        zoomControl: false,
        scrollWheelZoom: false
    }).setView([-1.9403, 29.8739], 8.5);

    // Clean minimal basemap tiles - ArcGIS Canvas with CartoDB fallback
    const tileLayer = L.tileLayer('https://services.arcgisonline.com/ArcGIS/rest/services/Canvas/World_Light_Gray_Base/MapServer/tile/{z}/{y}/{x}', {
        maxZoom: 16
    }).addTo(map);

    tileLayer.on('tileerror', () => {
        if (!map._fallbackAdded) {
            map._fallbackAdded = true;
            L.tileLayer('https://cartodb-basemaps-a.global.ssl.fastly.net/light_all/{z}/{x}/{y}.png', {
                maxZoom: 18
            }).addTo(map);
        }
    });

    // Invalidate size once DOM layout is settled
    setTimeout(() => { if (map) map.invalidateSize(); }, 150);
    setTimeout(() => { if (map) map.invalidateSize(); }, 500);
    window.addEventListener('resize', () => { if (map) map.invalidateSize(); });

    // Watermark Country Labels
    const neighbors = [
        { name: 'UGANDA', lat: -1.08, lng: 30.08 },
        { name: 'DRC', lat: -1.90, lng: 28.70 },
        { name: 'BURUNDI', lat: -2.80, lng: 29.85 },
        { name: 'TANZANIA', lat: -1.95, lng: 31.15 }
    ];
    neighbors.forEach(n => {
        L.marker([n.lat, n.lng], {
            icon: L.divIcon({
                className: 'country-watermark-label',
                html: n.name,
                iconSize: [80, 20],
                iconAnchor: [40, 10]
            }),
            interactive: false
        }).addTo(map);
    });

    // Custom Controls (+, -, Recenter)
    setupCustomControls();

    // Hook up Dropdown Selectors & Reset Button
    setupToolbarSelectors();

    // Hook up Legend Interactivity
    setupLegendInteractivity();

    // Hook up Header Global Search Bar
    setupHeaderSearchIntegration();

    // Fetch GeoJSON and Render
    fetch('/static/data/rwanda_districts.geojson')
        .then(res => {
            if (!res.ok) throw new Error(`HTTP ${res.status}`);
            return res.json();
        })
        .then(geojson => {
            geoLayer = L.geoJSON(geojson, {
                style: feature => {
                    const dName = feature.properties.shapeName || feature.properties.name || '';
                    const val = getIndicatorValue(dName);
                    const isPinned = (dName === pinnedDistrictName);
                    return {
                        color: isPinned ? '#0f172a' : '#ffffff',
                        weight: isPinned ? 3.0 : 1.2,
                        fillColor: getDistrictColor(val),
                        fillOpacity: isPinned ? 0.98 : 0.88
                    };
                },
                onEachFeature: (feature, layer) => {
                    const dName = feature.properties.shapeName || feature.properties.name || 'District';

                    layer.on('click', e => {
                        L.DomEvent.stopPropagation(e);
                        selectDistrict(dName, false);
                    });

                    layer.on('mouseover', () => {
                        layer.setStyle({
                            weight: 2.8,
                            color: '#0f172a',
                            fillOpacity: 0.96
                        });
                        layer.bringToFront();
                    });

                    layer.on('mouseout', () => {
                        if (geoLayer) {
                            geoLayer.resetStyle(layer);
                            if (pinnedDistrictName) {
                                highlightSelectedDistrict(pinnedDistrictName);
                            }
                        }
                    });
                }
            }).addTo(map);

            try {
                map.fitBounds(geoLayer.getBounds(), { padding: [16, 16] });
            } catch (e) {
                map.setView([-1.9403, 29.8739], 8.5);
            }

            setTimeout(() => { if (map) map.invalidateSize(); }, 150);

            // Select initial district (default: Nyabihu or URL parameter)
            updateLegendDisplay();
            updateBottomKpis();
            selectDistrict(pinnedDistrictName || 'Nyabihu', false);
        })
        .catch(err => {
            console.error("Error loading Rwanda GeoJSON:", err);
        });
}

/* ==========================================================================
   4. DISTRICT SELECTION & SIDEBAR UPDATES
   ========================================================================== */
function selectDistrict(dName, panTo = false) {
    if (!dName) return;
    pinnedDistrictName = dName;
    const center = DISTRICT_CENTROIDS[dName] || [-1.6687, 29.5115];

    if (panTo && map) {
        map.panTo(center, { animate: true, duration: 0.5 });
    }

    showPinnedDistrictPopup(center, dName);
    highlightSelectedDistrict(dName);
    updateDistrictDetailsCard(dName);
    updateUrlQueryState();
}

function showPinnedDistrictPopup(latlng, dName) {
    if (pinnedMarker) {
        map.removeLayer(pinnedMarker);
        pinnedMarker = null;
    }

    const val = getIndicatorValue(dName);
    const formattedVal = formatIndicatorValue(val);
    const indLabel = currentIndicator === 'production' ? 'Production' : (currentIndicator === 'area' ? 'Area' : 'Yield');

    const html = `
        <div class="district-dark-callout">
            <div class="callout-title">${dName} District</div>
            <div class="callout-value">${indLabel}: ${formattedVal}</div>
        </div>
    `;

    const customIcon = L.divIcon({
        className: 'custom-leaflet-callout-wrap',
        html: html,
        iconSize: [140, 52],
        iconAnchor: [70, 60]
    });

    pinnedMarker = L.marker(latlng, {
        icon: customIcon,
        interactive: false,
        zIndexOffset: 1000
    }).addTo(map);
}

function highlightSelectedDistrict(dName) {
    if (!geoLayer) return;
    geoLayer.eachLayer(layer => {
        const name = layer.feature.properties.shapeName || layer.feature.properties.name || '';
        const val = getIndicatorValue(name);
        if (name === dName) {
            layer.setStyle({
                weight: 3.2,
                color: '#0f172a',
                fillColor: getDistrictColor(val),
                fillOpacity: 0.98
            });
            layer.bringToFront();
        } else {
            layer.setStyle({
                weight: 1.2,
                color: '#ffffff',
                fillColor: getDistrictColor(val),
                fillOpacity: 0.88
            });
        }
    });
}

function updateDistrictDetailsCard(dName) {
    const province = DISTRICT_PROVINCE_MAP[dName] || 'Western Province';
    const metrics = getDistrictMetrics(dName);
    const seasonLabel = (MAP_SEASON_DATA[currentSeason] || {}).label || 'SAS 2024 – 2025';

    // Update Headings with micro-fade animation
    const nameEl = document.getElementById('card-district-name');
    const provEl = document.getElementById('card-province-name');
    if (nameEl) nameEl.textContent = `${dName} District`;
    if (provEl) provEl.textContent = province;

    // Update 5 Metrics
    const cropEl = document.getElementById('card-crop-name');
    const seasonEl = document.getElementById('card-season-name');
    const yieldEl = document.getElementById('card-yield-val');
    const areaEl = document.getElementById('card-area-val');
    const prodEl = document.getElementById('card-prod-val');

    if (cropEl) cropEl.textContent = currentCrop;
    if (seasonEl) seasonEl.textContent = seasonLabel;
    if (yieldEl) yieldEl.textContent = `${metrics.yield.toFixed(1)} t/ha`;
    if (areaEl) areaEl.textContent = `${metrics.area.toLocaleString()} ha`;
    if (prodEl) prodEl.textContent = `${metrics.prod.toLocaleString()} t`;

    // Update CTA Report Link
    const reportBtn = document.getElementById('btn-view-district-report');
    if (reportBtn) {
        const dId = DISTRICT_ID_MAP[dName] || 15;
        reportBtn.href = `/dashboard/reports/district/${dId}/`;
    }
}

/* Synchronize active state with browser URL */
function updateUrlQueryState() {
    const params = new URLSearchParams();
    if (currentCrop) params.set('crop', currentCrop);
    if (currentSeason) params.set('season', currentSeason);
    if (currentIndicator) params.set('indicator', currentIndicator);
    if (pinnedDistrictName) params.set('district', pinnedDistrictName);
    const newUrl = `${window.location.pathname}?${params.toString()}`;
    window.history.replaceState({}, '', newUrl);
}

/* ==========================================================================
   5. TOOLBAR SELECTORS & RESET CONTROLS
   ========================================================================== */
function setupToolbarSelectors() {
    const cropSel = document.getElementById('map-filter-crop');
    const seasonSel = document.getElementById('map-filter-season');
    const indicatorSel = document.getElementById('map-filter-indicator');
    const resetBtn = document.getElementById('btn-map-reset');

    if (cropSel) {
        cropSel.addEventListener('change', e => {
            currentCrop = e.target.value;
            applyDataRefresh();
            updateUrlQueryState();
        });
    }

    if (seasonSel) {
        seasonSel.addEventListener('change', e => {
            currentSeason = e.target.value;
            updateBottomKpis();
            applyDataRefresh();
            updateUrlQueryState();
        });
    }

    if (indicatorSel) {
        indicatorSel.addEventListener('change', e => {
            currentIndicator = e.target.value;
            updateLegendDisplay();
            applyDataRefresh();
            updateUrlQueryState();
        });
    }

    if (resetBtn) {
        resetBtn.addEventListener('click', () => {
            currentCrop = 'Maize';
            currentSeason = '2025A';
            currentIndicator = 'yield';
            pinnedDistrictName = 'Nyabihu';

            if (cropSel) cropSel.value = 'Maize';
            if (seasonSel) seasonSel.value = '2025A';
            if (indicatorSel) indicatorSel.value = 'yield';

            if (map && geoLayer) {
                map.fitBounds(geoLayer.getBounds(), { padding: [16, 16] });
            } else if (map) {
                map.setView([-1.9403, 29.8739], 8.5);
            }

            updateLegendDisplay();
            updateBottomKpis();
            applyDataRefresh();
            selectDistrict('Nyabihu', false);
            updateUrlQueryState();
        });
    }
}

function applyDataRefresh() {
    if (!geoLayer) return;
    geoLayer.eachLayer(layer => {
        const name = layer.feature.properties.shapeName || layer.feature.properties.name || '';
        const val = getIndicatorValue(name);
        const isPinned = (name === pinnedDistrictName);
        layer.setStyle({
            fillColor: getDistrictColor(val),
            color: isPinned ? '#0f172a' : '#ffffff',
            weight: isPinned ? 3.2 : 1.2,
            fillOpacity: isPinned ? 0.98 : 0.88
        });
    });

    if (pinnedDistrictName) {
        const center = DISTRICT_CENTROIDS[pinnedDistrictName] || [-1.6687, 29.5115];
        showPinnedDistrictPopup(center, pinnedDistrictName);
        updateDistrictDetailsCard(pinnedDistrictName);
    }
}

function updateLegendDisplay() {
    const titleEl = document.getElementById('legend-indicator-title');
    const listEl = document.getElementById('legend-scales-list');
    if (!titleEl || !listEl) return;

    if (currentIndicator === 'production') {
        titleEl.textContent = 'PRODUCTION (T)';
        listEl.innerHTML = `
            <div class="legend-scale-item" data-range="gt5000"><span class="legend-color-box" style="background: #15803d;"></span><span>> 5,000</span></div>
            <div class="legend-scale-item" data-range="3500-5000"><span class="legend-color-box" style="background: #22c55e;"></span><span>3,500 – 5,000</span></div>
            <div class="legend-scale-item" data-range="2000-3500"><span class="legend-color-box" style="background: #84cc16;"></span><span>2,000 – 3,500</span></div>
            <div class="legend-scale-item" data-range="1000-2000"><span class="legend-color-box" style="background: #eab308;"></span><span>1,000 – 2,000</span></div>
            <div class="legend-scale-item" data-range="lt1000"><span class="legend-color-box" style="background: #0284c7;"></span><span>< 1,000</span></div>
            <div class="legend-scale-item" data-range="nodata"><span class="legend-color-box" style="background: #cbd5e1;"></span><span>No data</span></div>
        `;
    } else if (currentIndicator === 'area') {
        titleEl.textContent = 'CULTIVATED AREA (HA)';
        listEl.innerHTML = `
            <div class="legend-scale-item" data-range="gt2000"><span class="legend-color-box" style="background: #15803d;"></span><span>> 2,000</span></div>
            <div class="legend-scale-item" data-range="1500-2000"><span class="legend-color-box" style="background: #22c55e;"></span><span>1,500 – 2,000</span></div>
            <div class="legend-scale-item" data-range="1000-1500"><span class="legend-color-box" style="background: #84cc16;"></span><span>1,000 – 1,500</span></div>
            <div class="legend-scale-item" data-range="500-1000"><span class="legend-color-box" style="background: #eab308;"></span><span>500 – 1,000</span></div>
            <div class="legend-scale-item" data-range="lt500"><span class="legend-color-box" style="background: #0284c7;"></span><span>< 500</span></div>
            <div class="legend-scale-item" data-range="nodata"><span class="legend-color-box" style="background: #cbd5e1;"></span><span>No data</span></div>
        `;
    } else {
        titleEl.textContent = 'YIELD (T/HA)';
        listEl.innerHTML = `
            <div class="legend-scale-item" data-range="gt4"><span class="legend-color-box" style="background: #15803d;"></span><span>> 4.0</span></div>
            <div class="legend-scale-item" data-range="3-4"><span class="legend-color-box" style="background: #22c55e;"></span><span>3.0 – 4.0</span></div>
            <div class="legend-scale-item" data-range="2-3"><span class="legend-color-box" style="background: #84cc16;"></span><span>2.0 – 3.0</span></div>
            <div class="legend-scale-item" data-range="1-2"><span class="legend-color-box" style="background: #eab308;"></span><span>1.0 – 2.0</span></div>
            <div class="legend-scale-item" data-range="lt1"><span class="legend-color-box" style="background: #0284c7;"></span><span>< 1.0</span></div>
            <div class="legend-scale-item" data-range="nodata"><span class="legend-color-box" style="background: #cbd5e1;"></span><span>No data</span></div>
        `;
    }
}

function updateBottomKpis() {
    const sData = MAP_SEASON_DATA[currentSeason] || MAP_SEASON_DATA['2025A'];
    const kpis = sData.kpiTotals;

    const cropsEl = document.getElementById('kpi-tracked-crops');
    const recordsEl = document.getElementById('kpi-validated-records');
    const geoEl = document.getElementById('kpi-geographic-coverage');
    const prodEl = document.getElementById('kpi-total-production');

    if (cropsEl) cropsEl.textContent = kpis.crops;
    if (recordsEl) recordsEl.textContent = kpis.records;
    if (geoEl) geoEl.textContent = kpis.districts;
    if (prodEl) prodEl.textContent = kpis.prod;
}

/* ==========================================================================
   6. INTERACTIVE LEGEND HOVER
   ========================================================================== */
function setupLegendInteractivity() {
    const legendEl = document.getElementById('map-legend');
    if (!legendEl) return;

    legendEl.addEventListener('mouseover', e => {
        const item = e.target.closest('.legend-scale-item');
        if (!item || !geoLayer) return;

        const colorBox = item.querySelector('.legend-color-box');
        if (!colorBox) return;
        const targetColorHex = colorBox.style.backgroundColor;

        geoLayer.eachLayer(layer => {
            const name = layer.feature.properties.shapeName || layer.feature.properties.name || '';
            const val = getIndicatorValue(name);
            const dColor = getDistrictColor(val);
            // Convert rgb to hex for comparison if necessary
            if (isColorMatch(dColor, targetColorHex)) {
                layer.setStyle({
                    fillOpacity: 1.0,
                    weight: 3.0,
                    color: '#0f172a'
                });
            } else {
                layer.setStyle({
                    fillOpacity: 0.22,
                    weight: 0.8,
                    color: '#ffffff'
                });
            }
        });
    });

    legendEl.addEventListener('mouseout', e => {
        if (!legendEl.contains(e.relatedTarget)) {
            applyDataRefresh();
        }
    });
}

function isColorMatch(hexColor, rgbOrHex) {
    if (!hexColor || !rgbOrHex) return false;
    const tempDiv = document.createElement('div');
    tempDiv.style.color = hexColor;
    const hexAsRgb = tempDiv.style.color;
    tempDiv.style.color = rgbOrHex;
    const targetAsRgb = tempDiv.style.color;
    return hexAsRgb === targetAsRgb;
}

/* ==========================================================================
   7. NAVBAR GLOBAL SEARCH BAR INTEGRATION
   ========================================================================== */
function setupHeaderSearchIntegration() {
    const searchInput = document.querySelector('.header-search-pill input');
    if (!searchInput) return;

    searchInput.addEventListener('input', e => {
        const query = (e.target.value || '').trim().toLowerCase();
        if (!query || query.length < 2) return;

        const match = Object.keys(DISTRICT_CENTROIDS).find(d => d.toLowerCase().startsWith(query)) ||
                      Object.keys(DISTRICT_CENTROIDS).find(d => d.toLowerCase().includes(query));
        if (match) {
            selectDistrict(match, true);
        }
    });

    searchInput.addEventListener('keydown', e => {
        if (e.key === 'Enter') {
            e.preventDefault();
            const query = (e.target.value || '').trim().toLowerCase();
            const match = Object.keys(DISTRICT_CENTROIDS).find(d => d.toLowerCase() === query) ||
                          Object.keys(DISTRICT_CENTROIDS).find(d => d.toLowerCase().includes(query));
            if (match) {
                selectDistrict(match, true);
            }
        }
    });
}

/* ==========================================================================
   8. CUSTOM MAP CONTROLS
   ========================================================================== */
function setupCustomControls() {
    const inBtn = document.getElementById('ctrl-zoom-in');
    const outBtn = document.getElementById('ctrl-zoom-out');
    const centerBtn = document.getElementById('ctrl-recenter');

    if (inBtn) inBtn.addEventListener('click', () => map && map.zoomIn());
    if (outBtn) outBtn.addEventListener('click', () => map && map.zoomOut());
    if (centerBtn) centerBtn.addEventListener('click', () => {
        if (map && geoLayer) {
            map.fitBounds(geoLayer.getBounds(), { padding: [16, 16] });
        } else if (map) {
            map.setView([-1.9403, 29.8739], 8.5);
        }
    });
}

