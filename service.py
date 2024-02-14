import parser
import sql_adapter


async def find_dc(vin_code):
    v = parser.VinDcCheck()
    vin = v.get_vin_code(vin_code)
    result = []
    if vin:
        if len(vin) == 1:
            vin = vin[0]
            resp = await sql_adapter.create_vin_act_dk(vin)
            if resp:
                result.append(await sql_adapter.find_vin_act_dk(vin_code))
            return result[0]
        elif len(vin) > 1:
            for item in vin:
                resp = await sql_adapter.create_vin_act_dk(item)
                if resp:
                    result.append(await sql_adapter.find_vin_act_dk(vin_code))
            return result
        else:
            return None
    else:
        print(f'Cant parse vin_code {vin_code}')
        return None


async def dc(vin_code):
    return await sql_adapter.find_vin_act_dk(vin_code)


async def dk_previous(vin_code):
    return await sql_adapter.find_vin_prev_dk(vin_code)
