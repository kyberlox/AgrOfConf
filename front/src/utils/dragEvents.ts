export const startDrag = (event: DragEvent, item: string | number) => {
    if(!event || !event.dataTransfer) return;
    event.dataTransfer.dropEffect = 'move';
    event.dataTransfer.effectAllowed = 'move';
    event.dataTransfer.setData('itemId', String(item))
    onLeave(event)
} 

export const onOver = (event: Event) => {
    const anchor = (event.target as HTMLDivElement);
     anchor.classList.contains('drag-el') ? anchor.classList.add('on-over') : anchor.parentElement?.classList.add('on-over')
    onLeave(event);
} 

export const onLeave = (event: Event) => {
     (event.target as HTMLDivElement).classList.remove('on-over')
} 

export const onDrop =  (event: DragEvent, items: {id: string | number}[], index: string | number) => {
    if(!event || !event.dataTransfer) return;
    const itemId = event.dataTransfer.getData('itemId')
    const item = items.find((item)=> item.id == itemId)
    if(!item) return;
    const itemPosition = items.findIndex((item) => item.id == itemId)
    items.splice(itemPosition, 1)
    items.splice(Number(index), 0, item)
    onLeave(event);
}
