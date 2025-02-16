import { landing_main } from "./pages/landing/landing.js";
import { profit_main } from "./pages/profit/profit.js";
import { proj_intro_main } from "./pages/proj_intro/proj_intro.js";
import { report_main } from "./pages/report/report.js";
import { stock_forecast_main } from "./pages/stock_forecast/stock_forecast.js";

export function router_main(page) {
    switch (page) {
        case 'landing':
            landing_main();
            break;
        case 'proj_intro':
            proj_intro_main();
            break;
        case 'stock_forecast':
            stock_forecast_main();
            break;
        case 'report':
            report_main();
            break;
        case 'profit':
            profit_main();
            break;
        default:
            console.log('올바르지 않은 페이지 id');
    }
}