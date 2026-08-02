(async function scanDynamicPetsFullJSON() {
    const CC = typeof cc !== 'undefined' ? cc : window.cc;
    if (!CC) return console.error("❌ 请确认控制台顶部已切换到 index.html！");

    const scene = CC.director.getScene();
    let listNode = null;
    let btnRightNode = null;
    let pageLabelNode = null;

    // 递归寻找关键 UI 节点
    function findNodes(n) {
        if (!n) return;
        if (n.name === "List") listNode = n;
        if (n.name === "btnRight") btnRightNode = n;
        // 尝试寻找带有数字显示的页码 Label 节点
        if (n.getComponent && n.getComponent(CC.Label)) {
            const txt = n.getComponent(CC.Label).string || "";
            if (txt.includes("/") && /\d+\/\d+/.test(txt)) {
                pageLabelNode = n;
            }
        }
        (n._children || n.children || []).forEach(findNodes);
    }
    findNodes(scene);

    if (!listNode || !btnRightNode) return console.error("❌ 未找到列表或右翻页按钮！");

    // 1. 动态获取当前分类的总页数 (例如从 "1/208" 中提取出 208)
    function getMaxPage() {
        if (pageLabelNode) {
            const txt = pageLabelNode.getComponent(CC.Label).string || "";
            const match = txt.match(/\/(\d+)/);
            if (match && match[1]) {
                return parseInt(match[1], 10);
            }
        }
        return 9999; // 如果没找到页码 Label，默认给个较大值，靠切页校验止损
    }

    const maxPage = getMaxPage();
    console.log(`🎯 识别到当前分类最高页码为: ${maxPage === 9999 ? '未知(将自动判定末页)' : maxPage + ' 页'}`);

    // 获取第一只宠物 ID 用于校验真实切页
    function getFirstPetId() {
        const items = listNode._children || listNode.children || [];
        if (!items[0]) return null;
        if (items[0]._components) {
            for (let c of items[0]._components) {
                const data = c.data || c._data || c.dataObject || c._dataObject || c.info;
                if (data && data.id) return data.id;
            }
        }
        return (items[0].dataObject || items[0]._dataObject || items[0].data || {}).id;
    }

    // 触发点击翻页
    function clickBtnRight() {
        if (!btnRightNode) return;
        if (CC.Node && CC.Node.EventType) {
            btnRightNode.emit(CC.Node.EventType.TOUCH_END, btnRightNode);
            btnRightNode.emit('click', btnRightNode);
        }
        if (btnRightNode._components) {
            btnRightNode._components.forEach(c => {
                if (c.clickEvents && Array.isArray(c.clickEvents)) {
                    c.clickEvents.forEach(evt => evt.emit([evt.customEventData]));
                }
                if (typeof c._onTouchEnded === 'function') c._onTouchEnded();
                if (typeof c._onPostHandler === 'function') c._onPostHandler();
            });
        }
    }

    const allPetList = [];
    const petIdSet = new Set();
    const sleep = ms => new Promise(res => setTimeout(res, ms));

    // 采集单页数据
    function scanAndPrintPage(page) {
        const items = listNode._children || listNode.children || [];
        const currentPagePets = [];

        items.forEach((item) => {
            let rawData = null;
            if (item._components) {
                for (let c of item._components) {
                    const d = c.data || c._data || c.dataObject || c._dataObject || c.info;
                    if (d && (d.name || d.id)) { rawData = d; break; }
                }
            }
            if (!rawData) {
                rawData = item.dataObject || item._dataObject || item.data || {};
            }

            const petId = rawData.id;
            const petName = rawData.name;

            if (!petId || !petName) return;

            // 检查灰度判断是否未点亮 (unknown)
            let isGrayscale = false;
            function checkGray(n) {
                if (n.name === "mcIcon" && n._components) {
                    for (let c of n._components) {
                        if (c.grayscale === true || c._grayscale === true) isGrayscale = true;
                    }
                }
                (n._children || n.children || []).forEach(checkGray);
            }
            checkGray(item);

            const unknown = isGrayscale;
            const isNew = Boolean(rawData.isNew || rawData.is_new || rawData._isNew || false);
            const isStarred = Boolean(rawData.isStarred || rawData.isStar || rawData._isStarred || false);

            const petObj = {
                page: page,
                id: petId,
                name: petName,
                unknown: unknown,
                isNew: isNew,
                isStarred: isStarred
            };

            if (!petIdSet.has(petId)) {
                petIdSet.add(petId);
                allPetList.push(petObj);
                currentPagePets.push(`${petName}(${unknown ? '未点亮' : '已点亮'})`);
            }
        });

        if (currentPagePets.length > 0) {
            console.log(`📄 第 ${page} 页抓取成功 (${currentPagePets.length} 只):`, currentPagePets.join(" | "));
        }
    }

    // 导出 JSON
    function saveToJsonFile(data) {
        const jsonString = JSON.stringify(data, null, 2);
        const blob = new Blob([jsonString], { type: "application/json" });
        const url = URL.createObjectURL(blob);

        const a = document.createElement("a");
        a.href = url;
        a.download = `pets_data_total_${data.length}_${new Date().getTime()}.json`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
    }

    console.log("⚡ 动态全量扫描开始！间隔 1.2 秒 / 页...");

    let currentPage = 1;
    let samePageCount = 0; // 连续无法切页计数

    while (currentPage <= maxPage) {
        const lastId = getFirstPetId();

        // 1. 采集并打印当前页
        scanAndPrintPage(currentPage);

        // 2. 如果已经到达最后一页，直接跳出循环
        if (currentPage >= maxPage) {
            console.log(`🏁 已到达最后一页 (第 ${currentPage} 页)，停止扫描。`);
            break;
        }

        // 3. 翻页
        clickBtnRight();

        // 4. 等待 1.2 秒
        let wait = 0;
        while (wait < 1200) {
            await sleep(150);
            wait += 150;
        }

        const currentFirstId = getFirstPetId();

        // 5. 判断是否成功切页
        if (currentFirstId === lastId) {
            // 补击一次
            clickBtnRight();
            await sleep(400);

            // 如果补击后依然没有改变，计数 +1
            if (getFirstPetId() === lastId) {
                samePageCount++;
                if (samePageCount >= 2) {
                    console.log(`🛑 检测到连续翻页无变化，判断已达到最终页，提前结束。`);
                    break;
                }
            } else {
                samePageCount = 0;
            }
        } else {
            samePageCount = 0;
        }

        currentPage++;
    }

    console.log(`🎉 扫描全部完成！共收集到 ${allPetList.length} 只宠物全量数据！`);
    console.table(allPetList);

    // 自动导出 JSON 文件
    saveToJsonFile(allPetList);
    window.__ALL_PETS_LIST__ = allPetList;
})();