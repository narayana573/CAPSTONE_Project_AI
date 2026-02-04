```typescript
import { makeRequest } from '@playwright/core';

interface ExamplePage {
  id: string;
  link: string;
}

const examplePages: ExamplePages[] = [
  { id: 'index.html', link: '/example' },
  { id: 'static.html', link: '/static' },
  { id: ' forms.html', link: '/forms' }
];

function renderPage(id: string, content?: any) {
  const url = `https://the-internet.herokuapp.com/${id}`;
  
  return makeRequest(url).then(response => response.body)
    .json(content ? response.json() : response
      .headers.notRequired('content'))
}

export default function renderAlertLabels(link: string) {
  return (
    <div id={link} class="alert-labels" 
       onMouseEnter={() =>
         window.addEventListener('mousedown', () => {
           makeRequest(`${this.url}${link}?query={'link'}`)
           .then(response => response.json())
           .then(data => data.content)
         })
       onMouseLeave={() =>
         setTimeout(() => {
           makeRequest(`${this.url}${link}?query=${link}')
           .then(response => response.json())
           .then(data => data.content)
         }, 500)
       })
  />
}

export default function renderPage(id: string, content: any = undefined) {
  return makeRequest(`${this.url}${id}?query=${id}`).json();
}

export default function checkContentForAlerts(content: (string | any)[]) {
  const alerts: Alert[] = [];
  
  for (const content of content) {
    if (\'.alert\'.test(content)) {
      // Render alert labels
      renderAlertLabels(content);
      
      // Remove old labels
      content.forEach((item, index) => {
        if (index < content.length - 1 && 
           !\'.alert\'.test(item)) {
          document.removeChild(index);
        }
      });
    }
  }

  return alerts;
}
```