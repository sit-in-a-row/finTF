import { router_main } from "../router.js";
import { checkDuplication, createElement } from "./utils.js";

// 사이드바 네비게이션 아이템
const sidebarItems = [
    {
        id: 'proj_intro',
        iconSrc: '../../../assets/icons/sideBar_proj_intro.svg',
        text: '프로젝트 소개'
    },
    {
        id: 'stock_forecast',
        iconSrc: '../../../assets/icons/sideBar_stock_forecast.svg',
        text: '종목 전망 검색'
    },
    {
        id: 'report',
        iconSrc: '../../../assets/icons/sideBar_report.svg',
        text: '보고서 조회'
    },
    {
        id: 'profit',
        iconSrc: '../../../assets/icons/sideBar_profit.svg',
        text: '수익률 조회'
    }
];

const router_link = ['proj_intro', 'stock_forecast'];

export function create_sideBar() {
    checkDuplication('sideBar_container');

    var sideBar_container = createElement('div', 'sideBar_container', 'sideBar_container');

    // 로고 생성
    var sideBar_logo = createElement('img', 'sideBar_logo', 'sideBar_logo');
    sideBar_logo.addEventListener('click', ()=>{
        router_main('landing');
    })

    sideBar_logo.src = '../../../assets/logos/PI_logo_black.svg';
    sideBar_container.appendChild(sideBar_logo);

    // AI 포트폴리오 현황
    var portfolio_container = createElement('div', 'sideBar_portfolio_container', 'sideBar_portfolio_container');

    var portfolio_title = createElement('div', 'sideBar_portfolio_title', 'sideBar_portfolio_title');
    portfolio_title.innerText = 'AI 포트폴리오 현황';
    portfolio_container.appendChild(portfolio_title);

    var portfolio_box = createElement('div', 'sideBar_portfolio_box', 'sideBar_portfolio_box');
    portfolio_container.appendChild(portfolio_box);
    sideBar_container.appendChild(portfolio_container);

    // 사이드바 아이템 생성
    var item_container = createElement('div', 'sideBar_item_container', 'sideBar_item_container');
    
    for (let i = 0; i < sidebarItems.length; i++) {
        const item = sidebarItems[i];
        const container = createElement('div', `sideBar_item_${item.id}`, `sideBar_item`);
        container.addEventListener('click', ()=>{
            router_main(router_link[i]);
        })

        const icon = createElement('img', `sideBar_item_${item.id}_icon`, `sideBar_item_icon`);
        const text = createElement('div', `sideBar_item_${item.id}_text`, `sideBar_item_text`);
    
        icon.src = item.iconSrc;
        text.innerText = item.text;
    
        container.appendChild(icon);
        container.appendChild(text);

        container.addEventListener('mouseover', () => {
            container.classList.add('sideBar_item_hover');
        })

        container.addEventListener('mouseout', () => {
            // container.style.transition = '0.1s';
            container.classList.remove('sideBar_item_hover');
        })
    
        item_container.appendChild(container);
    };
    sideBar_container.appendChild(item_container);

    var sideBar_bottom_container = createElement('div', 'sideBar_bottom_container', 'sideBar_bottom_container');
    var sideBar_bottom_img = createElement('img', 'sideBar_bottom_img', 'sideBar_bottom_img')
    sideBar_bottom_img.src = '../../../assets/icons/footer.svg'
    sideBar_bottom_container.appendChild(sideBar_bottom_img);

    sideBar_container.appendChild(sideBar_bottom_container);

    document.body.appendChild(sideBar_container);
}