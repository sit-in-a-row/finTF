import { checkDuplication, createElement } from "../../utils/utils.js";
import { create_sideBar } from "../../utils/sideBar.js";

export function proj_intro_main() {
    checkDuplication('landing_main');
    checkDuplication('proj_intro_container');
    checkDuplication('stock_forecast_container')

    const checkSideBar = document.getElementById('sideBar_container');
    if (!checkSideBar) {
        create_sideBar();
    }
    
    create_sideBar();
    create_proj_intro();
}

function create_proj_intro() {
    var proj_intro_container = createElement('div', 'proj_intro_container', 'proj_intro_container');

    var proj_intro_contents = createElement('img', 'proj_intro_contents', 'proj_intro_contents');
    proj_intro_contents.src = '../../../assets/imgs/proj_intro/paragraph.svg';
    proj_intro_container.appendChild(proj_intro_contents);

    document.body.appendChild(proj_intro_container);
}