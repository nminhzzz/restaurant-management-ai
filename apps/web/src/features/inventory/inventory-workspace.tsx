"use client";

import { useState } from "react";

import { PageHeader } from "@/components/page-states";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";

import { IssueList } from "./issue-list";
import { ReceiptList } from "./receipt-list";
import { StockTable } from "./stock-table";
import { StocktakePanel } from "./stocktake-panel";

export function InventoryWorkspace() {
  const [tab, setTab] = useState("stock");
  const [restockIngredientId, setRestockIngredientId] = useState<number | null>(
    null,
  );

  function restock(ingredientId: number) {
    setRestockIngredientId(ingredientId);
    setTab("receipts");
  }

  return (
    <div className="space-y-5">
      <PageHeader title="Kho" />
      <Tabs value={tab} onValueChange={setTab}>
        <TabsList>
          <TabsTrigger value="stock" className="h-9 px-4">
            Tồn kho
          </TabsTrigger>
          <TabsTrigger value="receipts" className="h-9 px-4">
            Phiếu nhập
          </TabsTrigger>
          <TabsTrigger value="issues" className="h-9 px-4">
            Phiếu xuất
          </TabsTrigger>
          <TabsTrigger value="stocktake" className="h-9 px-4">
            Kiểm kê
          </TabsTrigger>
        </TabsList>
        <TabsContent value="stock">
          <StockTable onRestock={restock} />
        </TabsContent>
        <TabsContent value="receipts">
          <ReceiptList
            prefillIngredientId={restockIngredientId}
            onPrefillHandled={() => setRestockIngredientId(null)}
          />
        </TabsContent>
        <TabsContent value="issues">
          <IssueList />
        </TabsContent>
        <TabsContent value="stocktake">
          <StocktakePanel />
        </TabsContent>
      </Tabs>
    </div>
  );
}
