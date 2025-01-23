import { router_main } from "../../router.js";
import { checkDuplication, createElement } from "../../utils/utils.js";

export function landing_main() {
    document.body.innerHTML = '';

    // 메인 컨테이너 생성 및 초기화
    const landing_main_container = createLandingMainContainer();

    // 상단 섹션 생성
    const landing_main_upper = createLandingMainUpper();
    landing_main_container.appendChild(landing_main_upper);

    // 카드 섹션 생성
    const landing_cards = createLandingCards();
    landing_main_container.appendChild(landing_cards);

    // 페이지에 포함
    document.body.appendChild(landing_main_container);

    // 3D 효과 및 호버 효과 추가
    add3DEffectAndHover();

    // TypeIt 애니메이션 추가
    addTypeItAnimation();
}

function createLandingMainContainer() {
    return createElement('div', 'landing_main', 'landing_main');
}

function createLandingMainUpper() {
    const landing_main_upper = createElement('div', 'landing_main_upper', 'landing_main_upper');

    // 프로메테우스 로고 요소 생성
    const PI_logo = createElement('img', 'PI_logo_landing', 'PI_logo_landing');
    PI_logo.src = '../../../assets/logos/PI_logo_black.svg';
    landing_main_upper.appendChild(PI_logo);

    // typeIt 요소 생성
    const typeIt = createElement('div', 'landing_typeIt', 'landing_typeIt');
    landing_main_upper.appendChild(typeIt);

    return landing_main_upper;
}

function createLandingCards() {
    const landing_cards = createElement('div', 'landing_card_container', 'landing_card_container');

    for (let i = 0; i < 4; i++) {
        const landing_card_element = createLandingCard(i);
        landing_cards.appendChild(landing_card_element);
    }

    return landing_cards;
}

function createLandingCard(index) {
    const landing_card_element = createElement('div', `landing_card_${index}`, 'landing_card_element');
    const landing_card_img = createElement('img', `landing_card_img_${index}`, 'landing_card_img');
    const landing_card_text = createElement('p', `landing_card_text_${index}`, 'landing_card_text');

    landing_card_img.src = `../../../assets/imgs/landing/${index}.svg`;

    // 카드 텍스트 설정
    switch (index) {
        case 0:
            landing_card_text.innerText = '프로젝트 소개';
            landing_card_element.addEventListener('click', ()=>{
                router_main('proj_intro');
            })
            break;
        case 1:
            landing_card_text.innerText = '종목 전망 검색';
            landing_card_element.addEventListener('click', ()=>{
                router_main('stock_forecast');
            })
            break;
        case 2:
            landing_card_text.innerText = '보고서 조회';
            break;
        case 3:
            landing_card_text.innerText = '수익률 조회';
            break;
    }

    // 이미지와 텍스트를 카드에 추가
    landing_card_element.appendChild(landing_card_img);
    landing_card_element.appendChild(landing_card_text);

    return landing_card_element;
}

function add3DEffectAndHover() {
    const images = document.querySelectorAll('.landing_card_img');

    document.body.addEventListener('mousemove', (e) => {
        const { clientX: mouseX, clientY: mouseY } = e;
        const centerX = window.innerWidth / 2;
        const centerY = window.innerHeight / 2;

        const rotateX = ((mouseY - centerY) / centerY) * -10; // 세로축 회전 각도
        const rotateY = ((mouseX - centerX) / centerX) * 10; // 가로축 회전 각도

        images.forEach(image => {
            image.style.transform = `perspective(1000px) rotateX(${rotateX}deg) rotateY(${rotateY}deg)`;
            image.style.transition = 'transform 0.1s ease-out';
        });
    });

    document.body.addEventListener('mouseleave', () => {
        images.forEach(image => {
            image.style.transform = 'perspective(1000px) rotateX(0deg) rotateY(0deg)';
            image.style.transition = 'transform 0.5s ease-out';
        });
    });

    images.forEach(image => {
        image.addEventListener('mouseenter', () => {
            const textElement = image.nextElementSibling; // 텍스트 요소 찾기

            // 텍스트 확대
            textElement.style.transform = 'scale(1.2)';
            textElement.style.transition = 'transform 0.1s ease-out';
            textElement.style.color = 'var(--color-white)';
        });

        image.addEventListener('mouseleave', () => {
            const textElement = image.nextElementSibling; // 텍스트 요소 찾기

            // 텍스트 원래 크기로 복원
            textElement.style.transform = 'scale(1)';
            textElement.style.transition = 'transform 0.5s ease-out';
            textElement.style.color = 'var(--color-darkGrey)';
        });
    });
}

// ["#LLM", "#Financial Engineering", "#Multi-Agents"],
function addTypeItAnimation() {
    new TypeIt("#landing_typeIt", {
        speed: 100,
        deleteSpeed: 50,
        breakLines: false,
        waitUntilVisible: true,
        loop: true,
        cursor: false, 
    })
    .type("#LLM", {delay: 1500})
    .delete(4)
    .type('#Financial Engineering', {delay: 1500})
    .delete(22)
    .type('#Multi-Agents', {delay: 1500})
    .delete(13)
    .go();
}