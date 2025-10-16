'use strict';

(function () {
    class PopupLoading extends HTMLElement {
        constructor() {
            super();

            this.attachShadow({ mode: 'open' });

            const wrapper = document.createElement('div');
            wrapper.setAttribute('class', 'wrapper');

            const windowElement = wrapper.appendChild(document.createElement('div'));
            windowElement.setAttribute('class', 'window');

            const loader = windowElement.appendChild(document.createElement('div'));
            loader.setAttribute('class', 'loader');

            const message = windowElement.appendChild(document.createElement('span'));
            message.setAttribute('class', 'text');
            message.setAttribute('role', 'status');
            message.setAttribute('aria-live', 'polite');
            message.textContent = this.dataset.message ? this.dataset.message : 'Loading';

            const style = document.createElement('style');
            style.textContent = `
                .wrapper {
                    width: 100%;
                    height: 100%;
                    display: flex;
                    flex-direction: column;
                    justify-content: center;
                    align-items: center;
                    background-color: #ffffff82;
                }

                .window {
                    padding: 10rem;
                    background-color: #ffffff8f;
                    border: 1px solid white;
                    border-radius: 1rem;
                    display: flex;
                    flex-direction: column;
                    justify-content: center;
                    align-items: center;
                }

                .loader {
                    border: 5px solid #f3f3f3;
                    border-radius: 50%;
                    border-top: 5px solid #009688;
                    width: 150px;
                    height: 150px;
                    -webkit-animation: spin 3s linear infinite;
                    animation: spin 3s cubic-bezier(.79,.14,.15,.86) infinite;
                }

                .text {
                    text-transform: uppercase;
                    padding: 1rem;
                    font-size: larger;
                    font-weight: lighter;
                    letter-spacing: 0.2rem;
                    color: #009688;
                }

                @-webkit-keyframes spin {
                    0% { -webkit-transform: rotate(0deg); }
                    100% { -webkit-transform: rotate(360deg); }
                }

                @keyframes spin {
                    0% { transform: rotate(0deg); }
                    50% { transform: rotate(360deg); border-inline-color: #009688; }
                    100% { transform: rotate(1080deg); }
                }
            `;

            this.shadowRoot.append(style, wrapper);
            this.animationTimeout = null;
        }

        static get observedAttributes() {
            return ['data-message'];
        }

        attributeChangedCallback(name, _oldValue, newValue) {
            if (name === 'data-message') {
                const shadow = this.shadowRoot;
                if (shadow) {
                    shadow.querySelector('.text').textContent = newValue ? newValue : 'Loading';
                }
            }
        }

        show() {
            this.style.display = 'block';
            this.animationTimeout = window.setTimeout(() => {
                this.style.opacity = '1';
            }, 10);
        }

        hide() {
            this.style.opacity = '0';
            this.animationTimeout = window.setTimeout(() => {
                this.style.display = 'none';
            }, 1000);
        }

        disconnectedCallback() {
            if (this.animationTimeout) {
                window.clearTimeout(this.animationTimeout);
            }
        }
    }

    if (!customElements.get('popup-loading')) {
        customElements.define('popup-loading', PopupLoading);
    }
}());
