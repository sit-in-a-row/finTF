import { checkDuplication } from "./utils.js";
import { create_sideBar } from "./sideBar.js";

export function clear_page() {
    checkDuplication('landing_main');
    checkDuplication('proj_intro_container');
    checkDuplication('stock_forecast_container');
    checkDuplication('report_container');
    checkDuplication('profit_container');

    const checkSideBar = document.getElementById('sideBar_container');
    if (!checkSideBar) {
        create_sideBar();
    }
}
