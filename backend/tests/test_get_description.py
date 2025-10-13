import xml.etree.ElementTree as ET
from backend.tasks.import_txc_new import get_description
from backend.transxchange.txc import Service


def test_get_description():
    element = ET.fromstring("""<Service CreationDateTime="2022-04-12T15:06:21" ModificationDateTime="2025-09-10T09:41:59" Modification="revise" RevisionNumber="2345">
      <ServiceCode>PH0005857:165</ServiceCode>
      <Lines>
        <Line id="SCSO:PH0005857:165:64">
          <LineName>64</LineName>
          <OutboundDescription>
            <Origin>Fulflood Peter Symonds</Origin>
            <Destination>Holybourne Eggars School</Destination>
            <Vias>
              <Via>Alresford, Four Marks</Via>
            </Vias>
            <Description>Fulflood Peter Symonds - Holybourne Eggars School</Description>
          </OutboundDescription>
          <InboundDescription>
            <Origin>Alton Station</Origin>
            <Destination>Fulflood Peter Symonds</Destination>
            <Vias>
              <Via>Four Marks, Alresford</Via>
            </Vias>
            <Description>Alton Station - Fulflood Peter Symonds</Description>
          </InboundDescription>
        </Line>
      </Lines>
      <OperatingPeriod>
        <StartDate>2025-09-11</StartDate>
      </OperatingPeriod>
      <TicketMachineServiceCode>9064</TicketMachineServiceCode>
      <RegisteredOperatorRef>3</RegisteredOperatorRef>
      <PublicUse>true</PublicUse>
      <StandardService>
        <Origin>Winchester</Origin>
        <Destination>Alton</Destination>
        <Vias>
          <Via>Morn Hill, Alresford, Four Marks</Via>
        </Vias>
        <UseAllStopPoints>false</UseAllStopPoints>
    
    </StandardService>
    </Service>
    
    """)

    service = Service(element, [], [])

    description = get_description(service)
    assert description == "Winchester - Alton"
