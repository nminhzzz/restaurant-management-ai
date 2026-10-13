"use client";

import { useState } from "react";

import { PageHeader } from "@/components/page-states";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";

import { useCanWrite } from "@/features/catalog/use-role";

import { DishWriteOff } from "./dish-write-off";
import { IssueList } from "./issue-list";
import { LotExpiryTable } from "./lot-expiry-table";
import { ReceiptList } from "./receipt-list";
import { StockTable } from "./stock-table";
import { StocktakePanel } from "./stocktake-panel";

// UX-only gate (FR-INV-06); the API enforces MANAGER/WAREHOUSE itself.
const DISH_WRITE_OFF_ROLES = ["MANAGER", "WAREHOUSE"];

export function InventoryWorkspace() {
  const canWriteOffDishes = useCanWrite(DISH_WRITE_OFF_ROLES);
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
          <TabsTrigger value="lots" className="h-9 px-4">
            Hạn sử dụng
          </TabsTrigger>
          <TabsTrigger value="receipts" className="h-9 px-4">
            Phiếu nhập
          </TabsTrigger>
          <TabsTrigger value="issues" className="h-9 px-4">
            Phiếu xuất
          </TabsTrigger>
          {canWriteOffDishes ? (
            <TabsTrigger value="dish-write-off" className="h-9 px-4">
              Hủy món
            </TabsTrigger>
          ) : null}
          <TabsTrigger value="stocktake" className="h-9 px-4">
            Kiểm kê
          </TabsTrigger>
        </TabsList>
        <TabsContent value="stock">
          <StockTable onRestock={restock} />
        </TabsContent>
        <TabsContent value="lots">
          <LotExpiryTable />
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
        {canWriteOffDishes ? (
          <TabsContent value="dish-write-off">
            <DishWriteOff />
          </TabsContent>
        ) : null}
        <TabsContent value="stocktake">
          <StocktakePanel />
        </TabsContent>
      </Tabs>
    </div>
  );
}
