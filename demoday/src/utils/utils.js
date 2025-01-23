// HTML 태그, id, 클래스
export function createElement(tag, id, className) {
    var element = document.createElement(tag);
    element.id = id;
    element.className = className;
    
    return element;
}

export function clearHTML(id) {
    var body = document.getElementById(id);
    body.innerHTML = '';
}

export function checkDuplication(id) {
    const element = document.getElementById(id);
    if (element && element.parentNode) {
        element.parentNode.removeChild(element);
    }
}